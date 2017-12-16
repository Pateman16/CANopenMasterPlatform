import numpy as np
from sklearn.cross_decomposition import PLSRegression
from motorModelPls import MotorPositionModel
from sklearn import linear_model

data = np.loadtxt('values.txt')
xdata = data[:, [0,1]]
ydata = data[:, [2,3]]
pls2 = PLSRegression(n_components=2)
pls2.fit(ydata, xdata)
polymodel = MotorPositionModel(data)

while(True):
    inpp = float(input("pitch"))
    inpr = float(input("roll"))
    pos = polymodel.getMotorPos(inpp,inpr)
    print("leftpos: {}, rightpos: {}".format(pos[0][0], pos[0][1]))

#X = [[0., 0.], [1., 1.], [2., 2.], [3., 3.]]
# univariate output
#Y = [0., 1., 2., 3.]
# multivariate output
#Z = [[0., 1.], [1., 2.], [2., 3.], [3., 4.]]

# ordinary least squares
#clf = linear_model.LinearRegression()
# univariate
#clf.fit(ydata, xdata)
#print(clf.predict ([[-0.9831303, 22.36476555]]))
# multivariate
#clf.fit(xdata, ydata)
#print(clf.predict([[0, 0.]]))

# Ridge
#clf = linear_model.BayesianRidge()
# univariate
#clf.fit(ydata, xdata)
#print(clf.predict ([[-0.9831303, 22.36476555]]))
# multivariate
#clf.fit(xdata, ydata)
#print(clf.predict([[0, 0.]]))

# Lasso
#clf = linear_model.Lasso()
# univariate
#clf.fit(ydata, xdata)
#print(clf.predict ([[-0.9831303, 22.36476555]]))
# multivariate
#clf.fit(xdata, ydata)
#print(clf.predict([[0, 0.]]))