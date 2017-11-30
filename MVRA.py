from sklearn import linear_model
from sklearn.preprocessing import PolynomialFeatures
import array
import pandas as pd
import numpy as np
#leftVal, rightVal, Roll, pitch

resultArr = np.empty(shape = [0,4])

for i in range (60):
    for j in range(60):
        resultArr = np.append(resultArr, [[i, j, i*2, j*2]], axis = 0)
print(resultArr)
df = pd.DataFrame(resultArr, columns=['leftVal','rightVal', 'Pitch', 'Roll'])
#print(df.get('Roll'))
#print(df.head())

x_train = resultArr[:, [2,3]]
yLeft_train = resultArr[:, [0]]
yRight_train = resultArr[:, [1]]

olsLeft = linear_model.LinearRegression()
olsRight = linear_model.LinearRegression()
olsLeft.fit(x_train, yLeft_train)
olsRight.fit(x_train, yRight_train)

poly = PolynomialFeatures(degree=2)
X_ = poly.fit_transform(x_train)
predict_ = poly.fit_transform([15.5,15])
clfLeft = linear_model.LinearRegression()
clfRight = linear_model.LinearRegression()
polyModelLeft = clfLeft.fit(X_, yLeft_train)
polyModelRight = clfRight.fit(X_, yRight_train)
#print(polyModelLeft.coef_)
#print(polyModelRight.coef_)
print (polyModelLeft.predict(predict_)[0][0])
print (polyModelRight.predict(predict_)[0])
#print model.predict(x_test)[0:5]