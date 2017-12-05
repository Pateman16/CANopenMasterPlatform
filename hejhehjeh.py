

while(True):
    leftpos = input('position left: ')
    if (leftpos == 'stop'):
        break
    rightpos = input('position right: ')

    leftpos = float(leftpos)
    rightpos = float(rightpos)
    if(rightpos > 120):
        rightpos = 120
    if(rightpos < 1):
        rightpos = 1
    if (leftpos > 120):
        leftpos = 120
    if (leftpos < 1):
        leftpos = 1


    print("going to leftposition: {} and rightposition: {}".format(leftpos, rightpos))

print("stopped")