from sklearn.cross_decomposition import PLSRegression


class MotorPositionModel(object):


    def __init__(self, dataset):
        pitchRoll = dataset[:, [2, 3]]
        motorPos = dataset[:, [0, 1]]

        self.polyModelLeft = PLSRegression(n_components=2)
        self.polyModelLeft.fit(pitchRoll, motorPos)


    def getMotorPos(self, pitch, roll):
        return self.polyModelLeft.predict([[pitch, roll]])