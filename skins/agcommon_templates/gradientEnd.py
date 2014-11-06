##parameters=startColor,count=1
##title=Calculate end gradient
from Products.agCommon import calculateGradient

startColor = startColor.replace('#', '')

for i in range(0,count):
    startColor = calculateGradient(startColor)

return '#' + startColor

