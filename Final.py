import numpy as np
import cv2
import imutils
from skimage.filters import threshold_local
from scipy.ndimage import morphology, label
import os

from random import randint

def documentScan(file, paperSize):
    ### FIND DOCUMENT
    # load image and create grayscale copy
    original = cv2.imread(file)
    gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    
    # save ratio of old height to new height
    ratio = gray.shape[0] / 500.0
    img = imutils.resize(gray, height = 500)

    # blur grayscale image and find edges
    img = cv2.GaussianBlur(img, (5, 5), 0)
    edges = cv2.Canny(img, 75, 200)

    ## FIND CORNERS OF DOCUMENT
    # find contours in image
    img2, cnts, hierachy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # sort contours by area and keep only the largest ones.
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]

    documentCoord = 0

    # loop through contours
    for c in cnts:
        # approximate the shape of each contour (number of points)
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
     
        # if our approximated contour has four points, then we can assume that we have found the document
        if len(approx) == 4:
            documentCoord = approx
            break

    # if no document was found
    if type(documentCoord) == int:
        return 0

    ## ORDER POINTS IN documentCoord
    # top left, top right, bottom right, bottom left
    orderPoints = np.zeros((4,2), dtype = 'float32')

    # scale coordinates for original image
    documentCoord = documentCoord.reshape(4, 2) * ratio # reshaped as documentCoord has an unnecessary third dimension

    # top left will have smallest sum of its coordinates and bottom right will have largest
    pointSums = documentCoord.sum(1)
    orderPoints[0] = documentCoord[np.argmin(pointSums)]
    orderPoints[2] = documentCoord[np.argmax(pointSums)]

    # top right will have smallest difference (largest negetive) and bottom left will smallest
    pointDiff = np.diff(documentCoord, axis = 1)
    orderPoints[1] = documentCoord[np.argmin(pointDiff)]
    orderPoints[3] = documentCoord[np.argmax(pointDiff)]

    ## PERFORM TRANSFORMATION
    # find largest distance between bottom and top of document (height)
    height1 = np.linalg.norm(orderPoints[0] - orderPoints[3])
    height2 = np.linalg.norm(orderPoints[1] - orderPoints[2])
    height = max(int(height1),int(height2))

    # find largest distance between left and right of document (width)
    width1 = np.linalg.norm(orderPoints[0] - orderPoints[1])
    width2 = np.linalg.norm(orderPoints[2] - orderPoints[3])
    width = max(int(width1),int(width2))
    
    # take into account size of paper if needed
    if paperSize != 0:
        if height > width:
            width = int(height * paperSize)
        else:
            height = int(width * paperSize)
      
    # new points for the image to be transformed to
    transformedPoints = np.array([[0,0],
                                  [width - 1, 0],
                                  [width - 1, height - 1],
                                  [0, height - 1]], dtype = 'float32')

    # create transformation matrix and apply it to image
    transformMatrix = cv2.getPerspectiveTransform(orderPoints, transformedPoints)
    transformedGray = cv2.warpPerspective(gray, transformMatrix, (width, height)) # this crops it aswell
    transformedOrig = cv2.warpPerspective(original, transformMatrix, (width, height))

    ### FIND OUTLINES
    # resize the image and save the ratio between the old and new height
    ratio = transformedGray.shape[1] / 700.0
    img = imutils.resize(transformedGray, width=700)

    T = threshold_local(img, 15, offset = 10, method = "gaussian")
    img = (img > T).astype("uint8") * 255

    img = np.invert(img)
    
    # find connected areas/features (blocks of pixels)
    lbl, num = label(img) # array of features, number of features

    ## DETERMINE IF OUTLINE
    # array where the coordinates of the outlines will be stored
    outlineBounds = []

    # loop through features
    for i in range(1, num + 1):
        # create two lists of the x and y coordinates (seperate) for all the pixels in the current feature
        py, px = np.nonzero(lbl == i)
        # find the minimum and maximum x and y coordinates
        xmin, xmax, ymin, ymax = px.min(), px.max(), py.min(), py.max()
        # calculate the height and width of the feature
        height = ymax - ymin
        width = xmax - xmin
        # only carry on if the feature is big enough
        if width > 40 and height > 40:

            # create boundary value as a tenth the shortest edge of the feature
            boundary = min(width,height)/10

            # variable for keeping track of whether feature is rectangular outline
            outline = True

            left = False
            right = False
            top = False
            bottom = False

            midw = xmin + int(width/2)
            midh = ymin + int(height/2)

            # loop through x and y coordinates of feature
            for e in range(py.size):
                # if any pixels are outside of the area between the minimum enclosing rectangle and the boundary within it, it's not an outline
                if px.item(e) > xmin + boundary and px.item(e) < xmax - boundary and py.item(e) > ymin + boundary and py.item(e) < ymax - boundary:
                    outline = False
                    break
            
                # check if the pixel is any of the four sides
                elif py.item(e) == midh and px.item(e) <= xmin + boundary and left == False:
                    left = True
                elif py.item(e) == midh and px.item(e) >= xmax - boundary and right == False:
                    right = True
                elif px.item(e) == midw and py.item(e) <= ymin + boundary and top == False:
                    top = True
                elif px.item(e) == midw and py.item(e) >= ymax - boundary and bottom == False:
                    bottom = True
                
            # there must be a pixel on each side otherwise it's not a pixel
            if left == False or right == False or top == False or bottom == False:
                outline = False
            
            # if the feature is an outline append its coordinates to the outlines array
            if outline == True:
                # two corners
                outlineBounds.append([int(ymin * ratio), int(ymax * ratio), int(xmin * ratio), int(xmax * ratio)])

    return outlineBounds, transformedGray, transformedOrig

def location(outline):
    # resize appropriately depending on the smallest dimesion
    dims = [outline.shape[0],outline.shape[1]]
    minDim = min(dims)

    if minDim >= 800:
        if minDim == dims[0]:
            outline = imutils.resize(outline, height=800)
        else:
            outline = imutils.resize(outline, width=800)

    # TESTING
    drawOutline = outline.copy()
    # TESTING

    # prepare outlines
    T = threshold_local(outline, 35, offset = 10, method = "gaussian")
    outline = (outline > T).astype("uint8") * 255

    outline = np.invert(outline)

    # TESTING
    cv2.imwrite('Testing/outlineThresh' + str(randint(0,1000)) + '.jpg', outline)
    # TESTING

    # find features
    lbl, num = label(outline)

    ## FIND CIRCLES
    for i in range(1, num + 1):
        # create two lists of the x and y coordinates (seperate) for all the pixels in the current feature
        py, px = np.nonzero(lbl == i)

        try:
            # find the minimum and maximum x and y coordinates
            xmin, xmax, ymin, ymax = px.min(), px.max(), py.min(), py.max()
        except ValueError:
            continue

        # calculate the height and width of the feature
        height = ymax - ymin
        width = xmax - xmin

        # minimum and maximum dimension
        minDim = min(height,width)
        maxDim = max(height,width)

        # height and width should closely represent a square (that's not too small)
        hwBoundary = maxDim/8
        if width > 45 and height > 45 and minDim >= maxDim - hwBoundary:

            # create inner circle boundary
            cBoundary = minDim/6

            # circle information
            radius = int(minDim/2)
            centre = (xmin + int(width/2), ymin + int(height/2))
            npCentre = np.array(centre)

            circle = True
            
            # loop through coordinates of feature and check if any point is outside the area enclosed by the inner and outer circle boundary
            for e in range(py.size):
                point = np.array([px.item(e), py.item(e)])
                distance = np.linalg.norm(centre - point)
                if distance < radius - cBoundary or distance > radius + cBoundary:
                    circle = False
                    break

            if circle == True:
                # four corners (fitting rectangle)
                #circles.append([int(ymin), int(ymax), int(xmin), int(xmax)])
                
                # prepare image
                circle = outline[int(ymin):int(ymax), int(xmin):int(xmax)]

                # TESTING
                circleNum = str(randint(0,1000))
                cv2.imwrite('Testing/circle' + circleNum + '.jpg', circle)
                # TESTING

                # apply label and find the second largest feature (symbol within circle)
                lbl, num = label(circle)

                largestArea = 0
                secondArea = 0
                secondBound = 0
                for i in range(1, num + 1):
                    py, px = np.nonzero(lbl == i)
                    xmin, xmax, ymin, ymax = px.min(), px.max(), py.min(), py.max()
                    # calculate the height, width and area of the feature
                    height = ymax - ymin
                    width = xmax - xmin
                    area = height*width
                    # find second largest
                    if area > largestArea:
                        largestArea = area
                    elif area > secondArea:
                        secondArea = area
                        secondBound = [ymin, ymax, xmin, xmax]
                        second = i
                
                # if the there is a second largest feature
                if secondBound != 0:
                    # remove all features from the image that aren't the second largest and convert the array into an image
                    lbl = lbl[secondBound[0]:secondBound[1], secondBound[2]:secondBound[3]]
                    lbl[lbl != second] = 0
                    lbl[lbl == second] = 255
                    symbol = np.array(lbl, dtype=np.uint8)

                    # TESTING
                    cv2.imwrite('Testing/symbol' + circleNum + '.jpg', symbol)
                    # TESTING
                    
                    #prepare the image similarly to how the symbols are stored
                    symbol = cv2.resize(symbol, (30,30))
                    symbol = symbol.reshape((1,900))
                    symbol = np.float32(symbol)
                    
                    # load the symbol images array
                    symbols = np.loadtxt('symbols/symbols.data', np.float32)

                    try:
                        symbols = symbols.reshape((1,900))
                    except ValueError:
                        pass
                    
                    # create an index array for each item in storedRef (KNearest responses has to be integers)
                    indexLength = symbols.shape[0]
                    symIndex = np.arange(indexLength)
                    symIndex = symIndex.reshape(symIndex.size, 1)

                    # create KNearest model and train it with symbols and symIndex (match based on order)
                    model = cv2.ml.KNearest_create()
                    model.train(symbols, cv2.ml.ROW_SAMPLE, symIndex)
                    
                    # find closest match between the symbol and a symbol stored
                    retval, results, neigh, dists = model.findNearest(symbol,1)

                    # locate associated path ot symbol and return it
                    index = int(results[0][0])

                    # TESTING
                    storedRef = np.genfromtxt('symbols/reference.data', dtype='str', delimiter=',')
                    try:
                        storedRef = storedRef.reshape((1,2))
                    except ValueError:
                        pass
                    print(storedRef.item(index, 0))
                    # TESTING

                    #return storedRef.item(index, 1)
                    return index

                # if there is no symbol inside the circle
                else:
                    continue

    # if no symbol found
    return '1'

def addSymbol(image, name, path):
    # prepare image
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    T = threshold_local(img, 355, offset = 10, method = "gaussian")
    img = (img > T).astype("uint8") * 255

    img = np.invert(img)

    #img = cv2.medianBlur(img,5)

    # apply label and find largest feature (symbol)
    lbl, num = label(img)

    largestArea = 0
    largest = 1
    for i in range(1, num + 1):
        py, px = np.nonzero(lbl == i)
        xmin, xmax, ymin, ymax = px.min(), px.max(), py.min(), py.max()
        # calculate the height, width and area of the feature
        height = ymax - ymin
        width = xmax - xmin
        area = height*width
        # find largest
        if area > largestArea:
            largestArea = area
            largest = i
            bound = [ymin, ymax, xmin, xmax]

    # remove all features from the image that aren't the largest and convert the array into an image
    lbl = lbl[bound[0]:bound[1], bound[2]:bound[3]]
    lbl[lbl != largest] = 0
    lbl[lbl == largest] = 255
    img = np.array(lbl, dtype=np.uint8)
    
    # reduce image to a large one dimensional array
    img = cv2.resize(img, (30,30))
    img = img.reshape((1,900))

    # if the reference file is populated, check the name isn't already in the reference file
    with open('symbols/reference.data', 'a') as ref:
        if os.stat('symbols/reference.data').st_size != 0:
            storedRef = np.genfromtxt('symbols/reference.data', dtype='str', delimiter=',')
            symbols = np.loadtxt('symbols/symbols.data', np.float32)

            try:
                symbols = symbols.reshape((1,900))
            except ValueError:
                pass

            try:
                storedRef = storedRef.reshape((1,2))
            except ValueError:
                pass

            indexLength = storedRef.shape[0]
        
            for symbol in range(indexLength):
                if storedRef[symbol][0] == name or np.array_equal(symbols[symbol], img[0]) == True:
                    return 0 
            
            symbols = np.append(symbols,img,0)
            np.savetxt('symbols/symbols.data', symbols)

            ref.write(name + ',' + path + '\n')
            
        else:
            ref.write(name + ',' + path + '\n')
            symbols = np.empty((0,900))
            symbols = np.append(symbols,img,0)
            np.savetxt('symbols/symbols.data', symbols)

def multAddSym(file):
    # prepare image
    orig = cv2.imread(file)

    ratio = orig.shape[0]/500

    orig = imutils.resize(orig, height=500)

    img = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)

    T = threshold_local(img, 95, offset = 10, method = "gaussian")
    img = (img > T).astype("uint8") * 255

    img = np.invert(img)

    # apply label and find features (symbols)
    lbl, num = label(img)

    symbols = []

    # loop through features
    for i in range(1, num + 1):
        py, px = np.nonzero(lbl == i)
        xmin, xmax, ymin, ymax = px.min(), px.max(), py.min(), py.max()
        height = ymax - ymin
        width = xmax - xmin
        area = height * width
        # only carry on if the feature is big enough
        if area > 200:
            
            if ymin - 10 >= 0:
                ymin = ymin - 10
            if ymax + 10 <= img.shape[0]:
                ymax = ymax + 10
            if xmin - 10 >= 0:
                xmin = xmin - 10
            if xmax + 10 <= img.shape[1]:
                xmax = xmax + 10
                
            symbols.append([int(ymin*ratio), int(ymax*ratio), int(xmin*ratio), int(xmax*ratio)])

    return symbols

def deleteSymbol(img):
    storedRef = np.genfromtxt('symbols/reference.data', dtype='str', delimiter=',')
    symbols = np.loadtxt('symbols/symbols.data', np.float32)

    try:
        symbols = symbols.reshape((1,900))
    except ValueError:
        pass

    try:
        storedRef = storedRef.reshape((1,2))
    except ValueError:
        pass

    storedRef = np.delete(storedRef, img, 0)
    symbols = np.delete(symbols, img, 0)

    np.savetxt('symbols/reference.data', storedRef, fmt='%s', delimiter=',')
    np.savetxt('symbols/symbols.data', symbols)

def editSymbol(img, name, path):
    storedRef = np.genfromtxt('symbols/reference.data', dtype='str', delimiter=',')

    try:
        storedRef = storedRef.reshape((1,2))
    except ValueError:
        pass

    for symbol in range(storedRef.shape[0]):
        if storedRef[symbol][0] == name and symbol != img:
            return 0 
    
    storedRef[img][0] = name
    storedRef[img][1] = path
    np.savetxt('symbols/reference.data', storedRef, fmt='%s', delimiter=',')
    
'''
file = input('Image: ')
name = input('Name: ')
path = input('Path: ')

addSymbol(file, name, path)
'''
'''
file = input('Image: ')
size = [int(i) for i in input('Paper size: ').split()]

doc = transform(file, size)
scan = documentScan(doc[0])

for i in range(len(scan)):
    cv2.imshow(str(i), doc[1][scan[i][0][0]:scan[i][0][1], scan[i][0][2]:scan[i][0][3]])
'''
