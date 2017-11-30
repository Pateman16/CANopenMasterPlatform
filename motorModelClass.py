from sklearn import linear_model
from sklearn.preprocessing import PolynomialFeatures
import pandas as pd
import numpy as np



class MotorPositionModel(object):


    def __init__(self, dataset):
        PitchRoll = dataset[:, [2, 3]]
        leftMotorPos = dataset[:, [0]]
        rightMotorPos = dataset[:, [1]]

        olsLeft = linear_model.LinearRegression()
        olsRight = linear_model.LinearRegression()
        olsLeft.fit(PitchRoll, leftMotorPos)
        olsRight.fit(PitchRoll, rightMotorPos)

        self.poly = PolynomialFeatures(degree=6)
        X_ = self.poly.fit_transform(PitchRoll)
        clfLeft = linear_model.LinearRegression()
        clfRight = linear_model.LinearRegression()
        self.polyModelLeft = clfLeft.fit(X_, leftMotorPos)
        self.polyModelRight = clfRight.fit(X_, rightMotorPos)

    def getLeftpos(self, pitch, roll):
        position_ = self.poly.fit_transform([[pitch, roll]])
        return self.polyModelLeft.predict(position_)[0][0]
    def getRightpos(self, pitch, roll):
        position_ = self.poly.fit_transform([[pitch, roll]])
        return self.polyModelRight.predict(position_)[0][0]