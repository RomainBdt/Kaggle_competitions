# %%
import pandas as pd
import numpy as np
import time
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import cohen_kappa_score, make_scorer
from functools import partial
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

# import classifiers
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, AdaBoostClassifier, GradientBoostingClassifier, BaggingClassifier
from sklearn.neighbors import KNeighborsClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier, SGDClassifier, PassiveAggressiveClassifier, Perceptron, RidgeClassifier, LogisticRegression
from sklearn.svm import SVC, LinearSVC, NuSVC
from sklearn.naive_bayes import GaussianNB, BernoulliNB, MultinomialNB, ComplementNB
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis, LinearDiscriminantAnalysis

# import regressors
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, AdaBoostRegressor, GradientBoostingRegressor, BaggingRegressor
from sklearn.neighbors import KNeighborsRegressor
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor, XGBRFRegressor
from catboost import CatBoostRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import LinearRegression, Ridge, SGDRegressor, PassiveAggressiveRegressor, Perceptron, RidgeClassifier, LogisticRegression
from sklearn.linear_model import Lasso, ElasticNet, Lars, BayesianRidge, ARDRegression, OrthogonalMatchingPursuit, HuberRegressor, TheilSenRegressor, RANSACRegressor
from sklearn.linear_model import LassoLars, LassoLarsIC
from sklearn.neural_network import MLPRegressor
from sklearn.gaussian_process import GaussianProcessRegressor

# %%
train = pd.read_csv('datasets/train.csv')
train.drop('Id', axis=1, inplace=True)
orig_train = pd.read_csv('datasets/WineQT.csv')
orig_train.drop('Id', axis=1, inplace=True)
X_test = pd.read_csv('datasets/test.csv')
X_test.drop('Id', axis=1, inplace=True)
len_test = X_test.shape[0]
red_wine = pd.read_csv('datasets/winequality-red.csv')

RUN_FOR_FINAL_PREDICTION = True

# Split data
X_train, X_val = train_test_split(train, test_size=0.2, random_state=42, stratify=train['quality'])
y_val = X_val.pop('quality')

# Add origin data
X_train = pd.concat([X_train, orig_train, red_wine]).reset_index(drop=True)
X_train.drop_duplicates(inplace=True)

# # Outlier removal
# print(X_train.shape)
# X_train = X_train[X_train['volatile acidity'] <= 1.33]
# X_train = X_train[X_train['citric acid'] <= 0.8]
# X_train = X_train[X_train['residual sugar'] < 9]
# X_train = X_train[X_train['chlorides'] <= 0.5]
# X_train = X_train[X_train['total sulfur dioxide'] <= 200]
# X_train = X_train[X_train['sulphates'] < 1.9]
# X_train = X_train[X_train['alcohol'] <= 14]
# print(X_train.shape)

y_train = X_train.pop('quality')

# Data preprocessing
def add_features(df):
    # From https://www.kaggle.com/competitions/playground-series-s3e5/discussion/383685
    df['acidity_ratio'] = df['fixed acidity'] / df['volatile acidity']
    df['free_sulfur/total_sulfur'] = df['free sulfur dioxide'] / df['total sulfur dioxide']
    df['sugar/alcohol'] = df['residual sugar'] / df['alcohol']
    df['alcohol/density'] = df['alcohol'] / df['density']
    df['total_acid'] = df['fixed acidity'] + df['volatile acidity'] + df['citric acid']
    df['sulphates/chlorides'] = df['sulphates'] / df['chlorides']
    df['bound_sulfur'] = df['total sulfur dioxide'] - df['free sulfur dioxide']
    df['alcohol/pH'] = df['alcohol'] / df['pH']
    df['alcohol/acidity'] = df['alcohol'] / df['total_acid']
    df['alkalinity'] = df['pH'] + df['alcohol']
    df['mineral'] = df['chlorides'] + df['sulphates'] + df['residual sugar']
    df['density/pH'] = df['density'] / df['pH']
    df['total_alcohol'] = df['alcohol'] + df['residual sugar']
    
    # From https://www.kaggle.com/competitions/playground-series-s3e5/discussion/382698
    df['acid/density'] = df['total_acid']  / df['density']
    df['sulphate/density'] = df['sulphates']  / df['density']
    df['sulphates/acid'] = df['sulphates'] / df['volatile acidity']
    df['sulphates*alcohol'] = df['sulphates'] * df['alcohol']
    
    return df

for df in [X_train, X_val, X_test]:
    df = add_features(df)
    
# Label encode
min_y = min(y_train.min(), y_val.min())
y_train -= min_y
y_val -= min_y

if RUN_FOR_FINAL_PREDICTION:
    X_train = pd.concat([X_train, X_val]).reset_index(drop=True)
    y_train = pd.concat([y_train, y_val]).reset_index(drop=True)
    
# Standardize
# scaler = StandardScaler()
# X_train = scaler.fit_transform(X_train)
# X_val = scaler.transform(X_val)
# X_test = scaler.transform(X_test)

# PCA (does not improve score)
# from sklearn.decomposition import PCA
# pca = PCA()
# X_train = pca.fit_transform(X_train)
# X_val = pca.transform(X_val)
# X_test = pca.transform(X_test)

# %% Classifiers

# classifiers = {
#     'LGBMClassifier': LGBMClassifier(random_state=42, n_jobs=-1),
#     'XGBClassifier': XGBClassifier(random_state=42, n_jobs=-1),
#     # 'CatBoostClassifier': CatBoostClassifier(random_state=42, silent=True),
#     'RandomForestClassifier': RandomForestClassifier(random_state=42, n_jobs=-1),
#     'ExtraTreesClassifier': ExtraTreesClassifier(random_state=42, n_jobs=-1),
#     # 'AdaBoostClassifier': AdaBoostClassifier(random_state=42),
#     'GradientBoostingClassifier': GradientBoostingClassifier(random_state=42),
#     'BaggingClassifier': BaggingClassifier(random_state=42, n_jobs=-1),
#     'KNeighborsClassifier': KNeighborsClassifier(n_jobs=-1),
#     # 'DecisionTreeClassifier': DecisionTreeClassifier(random_state=42),
#     'GaussianNB': GaussianNB(),
#     'LinearDiscriminantAnalysis': LinearDiscriminantAnalysis(),
#     'QuadraticDiscriminantAnalysis': QuadraticDiscriminantAnalysis(),
#     'LogisticRegression': LogisticRegression(random_state=42, n_jobs=-1),
#     'SVC': SVC(random_state=42, gamma='scale'),
#     # 'NuSVC': NuSVC(random_state=42, probability=True, gamma='scale'),
#     'LinearSVC': LinearSVC(random_state=42, max_iter=10000),
#     'MLPClassifier': MLPClassifier(random_state=42, max_iter=1000),
#     'RidgeClassifier': RidgeClassifier(random_state=42),
#     # 'SGDClassifier': SGDClassifier(random_state=42, max_iter=1000, tol=1e-3),
#     # 'PassiveAggressiveClassifier': PassiveAggressiveClassifier(random_state=42, max_iter=1000, tol=1e-3),
#     # 'Perceptron': Perceptron(random_state=42, max_iter=1000, tol=1e-3),
#     'GaussianProcessClassifier': GaussianProcessClassifier(random_state=42),
#     # 'BernoulliNB': BernoulliNB(),
#     # 'ComplementNB': ComplementNB(),
#     # 'MultinomialNB': MultinomialNB(),
#     # 'DummyClassifier': DummyClassifier(random_state=42),  
# }

# def scorer(estimator, X, y):
#     y_pred = estimator.predict(X)
#     return cohen_kappa_score(y, y_pred, weights='quadratic')

# import time

# results = []
# cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
# print('{: >30} {: >10} {: >10} {: >10} {: >10} {: >10} {: >10}'.format('Model', 'CV mean', 'CV std', 'CV min', 'Time', 'Train', 'Val'))
# for model_name, model in classifiers.items():
#     t0 = time.time()
#     scores_cv = cross_val_score(model, X_train, y_train, cv=cv, scoring=scorer, n_jobs=-1)
#     results.append(scores_cv)
#     model.fit(X_train, y_train)
#     score_train = scorer(model, X_train, y_train)
#     score_val = scorer(model, X_val, y_val)
#     row = ['%s' % model_name, 
#            '%.3f' % scores_cv.mean(), 
#            '%.3f' % scores_cv.std(),
#            '%.3f' % (scores_cv.mean() - scores_cv.std()),
#            '%.3f' % (time.time() - t0),
#            '%.3f' % score_train,
#            '%.3f' % score_val
#            ]
#     print('{: >30} {: >10} {: >10} {: >10} {: >10} {: >10} {: >10}'.format(*row))

# plt.figure(figsize=(25, 15))
# plt.boxplot(results, labels=classifiers.keys(), showmeans=True)
# plt.show()



# %% Regressors

regressors = {
    # 'LGBMRegressor1': LGBMRegressor(random_state=42, n_jobs=-1, boosting_type='gbdt'),
    # 'LGBMRegressor2': LGBMRegressor(random_state=42, n_jobs=-1, boosting_type='dart'),
    # 'LGBMRegressor3': LGBMRegressor(random_state=42, n_jobs=-1, boosting_type='goss'),
    'LGBMRegressor4': LGBMRegressor(random_state=42, n_jobs=-1, boosting_type='rf', subsample=.632, subsample_freq=1),
    # 'LGBMRegressor5': LGBMRegressor(random_state=42, n_jobs=-1, class_weight='balanced'),
    # 'LGBMRegressor6': LGBMRegressor(random_state=42, n_jobs=-1, subsample=0.7),
    # 'LGBMRegressor7': LGBMRegressor(random_state=42, n_jobs=-1, colsample_bytree=0.7),
    # 'LGBMRegressor8': LGBMRegressor(random_state=42, n_jobs=-1, subsample=0.7, colsample_bytree=0.7),
    # 'LGBMRegressor9': LGBMRegressor(random_state=42, n_jobs=-1, boosting_type='dart', colsample_bytree=0.7),
    # 'XGBRegressor1': XGBRegressor(random_state=42, n_jobs=-1),
    # 'XGBRegressor2': XGBRegressor(random_state=42, n_jobs=-1, booster='dart'),
    # 'XGBRegressor3': XGBRegressor(random_state=42, n_jobs=-1, booster='gblinear'),
    # 'XGBRegressor4': XGBRegressor(random_state=42, n_jobs=-1, colsample_bytree=0.7),
    # 'XGBRegressor5': XGBRegressor(random_state=42, n_jobs=-1, subsample=0.7),
    'XGBRandomForestRegressor': XGBRFRegressor(random_state=42, n_jobs=-1),
    # 'CatBoostRegressor': CatBoostRegressor(random_state=42, silent=True),
    'RandomForestRegressor': RandomForestRegressor(random_state=42, n_jobs=-1),
    'ExtraTreesRegressor': ExtraTreesRegressor(random_state=42, n_jobs=-1),
    # 'AdaBoostRegressor': AdaBoostRegressor(random_state=42),
    # 'GradientBoostingRegressor': GradientBoostingRegressor(random_state=42),
    # 'BaggingRegressor': BaggingRegressor(random_state=42, n_jobs=-1),
    # 'KNeighborsRegressor': KNeighborsRegressor(n_jobs=-1),
    # 'DecisionTreeRegressor': DecisionTreeRegressor(random_state=42),
    # 'GaussianProcessRegressor': GaussianProcessRegressor(random_state=42),
    # 'MLPRegressor1': MLPRegressor(random_state=42, max_iter=1000, activation='relu', solver='adam'),
    # 'MLPRegressor2': MLPRegressor(random_state=42, max_iter=1000, activation='relu', solver='lbfgs'),
    # 'MLPRegressor3': MLPRegressor(random_state=42, max_iter=5000, activation='tanh', solver='adam'),
    # 'MLPRegressor4': MLPRegressor(random_state=42, max_iter=1000, activation='tanh', solver='lbfgs'),
    # 'MLPRegressor5': MLPRegressor(random_state=42, max_iter=5000, activation='logistic', solver='adam'),
    # 'MLPRegressor6': MLPRegressor(random_state=42, max_iter=1000, activation='logistic', solver='lbfgs'),
    # 'MLPRegressor7': MLPRegressor(random_state=42, max_iter=5000, activation='identity', solver='adam'),
    # 'MLPRegressor8': MLPRegressor(random_state=42, max_iter=5000, activation='identity', solver='lbfgs'),
    # 'Ridge': Ridge(random_state=42),
    # 'SGDRegressor': SGDRegressor(random_state=42, max_iter=1000, tol=1e-3),
    # 'PassiveAggressiveRegressor': PassiveAggressiveRegressor(random_state=42, max_iter=1000, tol=1e-3),
    # 'Perceptron': Perceptron(random_state=42, max_iter=1000, tol=1e-3),
    # 'LinearRegression': LinearRegression(),
    # 'Lasso': Lasso(random_state=42),
    # 'ElasticNet': ElasticNet(random_state=42),
    # 'HuberRegressor': HuberRegressor(max_iter=1000),
    # 'BayesianRidge': BayesianRidge(),
    # 'ARDRegression': ARDRegression(),
    # 'TheilSenRegressor': TheilSenRegressor(random_state=42),
    # 'RANSACRegressor': RANSACRegressor(random_state=42),
    # 'OrthogonalMatchingPursuit': OrthogonalMatchingPursuit(normalize=False),
    # 'Lars': Lars(),
    # 'LassoLars': LassoLars(),
    # 'LassoLarsIC': LassoLarsIC(normalize=False),
}

# %% Regression with OptimizedRounder
class OptimizedRounder(object):
    def __init__(self):
        self.coef_ = 0

    def _kappa_loss(self, coef, X, y):
        X_p = np.copy(X)
        for i, pred in enumerate(X_p):
            if pred < coef[0]:
                X_p[i] = 0
            elif pred >= coef[0] and pred < coef[1]:
                X_p[i] = 1
            elif pred >= coef[1] and pred < coef[2]:
                X_p[i] = 2
            elif pred >= coef[2] and pred < coef[3]:
                X_p[i] = 3
            elif pred >= coef[3] and pred < coef[4]:
                X_p[i] = 4
            else:
                X_p[i] = 5

        ll = cohen_kappa_score(y, X_p, weights='quadratic')
        return -ll

    def fit(self, X, y):
        loss_partial = partial(self._kappa_loss, X=X, y=y)
        initial_coef = [0.5, 1.5, 2.5, 3.5, 4.5]
        self.coef_ = sp.optimize.minimize(loss_partial, initial_coef, method='nelder-mead')

    def predict(self, X, coef):
        X_p = np.copy(X)
        for i, pred in enumerate(X_p):
            if pred < coef[0]:
                X_p[i] = 0
            elif pred >= coef[0] and pred < coef[1]:
                X_p[i] = 1
            elif pred >= coef[1] and pred < coef[2]:
                X_p[i] = 2
            elif pred >= coef[2] and pred < coef[3]:
                X_p[i] = 3
            elif pred >= coef[3] and pred < coef[4]:
                X_p[i] = 4
            else:
                X_p[i] = 5
        return X_p

    def coefficients(self):
        return self.coef_['x']
    
class OptimizedRounder_v2(object):
    def __init__(self):
        self.coef_ = 0
    
    def _kappa_loss(self, coef, X, y):
        preds = pd.cut(X, [-np.inf] + list(np.sort(coef)) + [np.inf], labels = [0, 1, 2, 3, 4, 5])
        return -cohen_kappa_score(y, preds, weights = 'quadratic')
    
    def fit(self, X, y):
        loss_partial = partial(self._kappa_loss, X = X, y = y)
        initial_coef = [0.5, 1.5, 2.5, 3.5, 4.5]
        self.coef_ = sp.optimize.minimize(loss_partial, initial_coef, method = 'nelder-mead')
    
    def predict(self, X, coef):
        preds = pd.cut(X, [-np.inf] + list(np.sort(coef)) + [np.inf], labels = [0, 1, 2, 3, 4, 5])
        return preds
    
    def coefficients(self):
        return self.coef_['x']
    
def scorer(estimator, X, original_labels):
    regression_predictions = estimator.predict(X)
    optR = OptimizedRounder_v2()
    optR.fit(regression_predictions, original_labels)
    y_pred = optR.predict(regression_predictions, optR.coefficients())
    return cohen_kappa_score(original_labels, y_pred, weights='quadratic')

results = []
val_predictions = pd.DataFrame()
test_predictions = pd.DataFrame()
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
print('{: >30} {: >10} {: >10} {: >10} {: >10} {: >10} {: >10}'.format('Model', 'CV mean', 'CV std', 'CV min', 'Time', 'Train', 'Val'))
for model_name, model in regressors.items():
    t0 = time.time()
    scores_cv = cross_val_score(model, X_train, y_train, cv=cv, scoring=scorer, n_jobs=-1)
    results.append(scores_cv)
    model.fit(X_train, y_train)
    score_train = scorer(model, X_train, y_train)
    score_val = scorer(model, X_val, y_val)
    
    # round predictions for validation and test sets
    optR = OptimizedRounder_v2()
    optR.fit(model.predict(X_train), y_train)
    
    y_pred_val = model.predict(X_val)
    y_pred_val = optR.predict(y_pred_val, optR.coefficients())
    val_predictions[model_name] = y_pred_val
    
    y_pred_test = model.predict(X_test)
    y_pred_test = optR.predict(y_pred_test, optR.coefficients())
    test_predictions[model_name] = y_pred_test
    
    row = ['%s' % model_name, 
           '%.3f' % scores_cv.mean(), 
           '%.3f' % scores_cv.std(),
           '%.3f' % (scores_cv.mean() - scores_cv.std()),
           '%.3f' % (time.time() - t0),
           '%.3f' % score_train,
           '%.3f' % score_val
           ]
    print('{: >30} {: >10} {: >10} {: >10} {: >10} {: >10} {: >10}'.format(*row))

plt.figure(figsize=(25, 15))
plt.boxplot(results, labels=regressors.keys(), showmeans=True)
plt.show()

# %% Regression with distributed predictions
# def distribute_predictions(y_true, y_pred):
#     y_pred_sorted = pd.Series(y_pred).sort_values()    
#     freq_by_quality = (y_true.value_counts() / len(y_true)).sort_index()

#     # map quality to cumulative frequency
#     cum_sum_by_quality = freq_by_quality.cumsum()

#     # make new predictions with the same distribution as the original labels
#     y_pred_distributed = pd.Series([0] * len(y_pred_sorted))
#     start_index = 0
#     for quality, freq_threshold in cum_sum_by_quality.items():
#         end_index = round(freq_threshold * len(y_pred_sorted))
#         # print(quality, start_index, end_index)
#         y_pred_distributed.iloc[start_index:end_index] = quality
#         start_index = end_index
#     y_pred_distributed.index = y_pred_sorted.index
#     return y_pred_distributed.sort_index()

# def scorer(estimator, X, original_labels):
#     regression_predictions = estimator.predict(X)
#     y_pred = distribute_predictions(original_labels, regression_predictions)
#     return cohen_kappa_score(original_labels, y_pred, weights='quadratic')

# results = []
# val_predictions = pd.DataFrame()
# test_predictions = pd.DataFrame()

# cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
# print('{: >30} {: >10} {: >10} {: >10} {: >10} {: >10} {: >10}'.format('Model', 'CV mean', 'CV std', 'CV min', 'Time', 'Train', 'Val'))
# for model_name, model in regressors.items():
#     t0 = time.time()
#     scores_cv = cross_val_score(model, X_train, y_train, cv=cv, scoring=scorer, n_jobs=-1)
#     results.append(scores_cv)
#     model.fit(X_train, y_train)
#     score_train = scorer(model, X_train, y_train)
#     score_val = scorer(model, X_val, y_val)
#     pred_val = model.predict(X_val)
#     pred_val = distribute_predictions(y_train, pred_val)
#     val_predictions[model_name] = pred_val
    
#     if RUN_FOR_FINAL_PREDICTION:
#         pred_test = model.predict(X_test)
#         pred_test = distribute_predictions(y, pred_test)
#         test_predictions[model_name] = pred_test
    
#     row = ['%s' % model_name, 
#            '%.3f' % scores_cv.mean(), 
#            '%.3f' % scores_cv.std(),
#            '%.3f' % (scores_cv.mean() - scores_cv.std()),
#            '%.3f' % (time.time() - t0),
#            '%.3f' % score_train,
#            '%.3f' % score_val
#            ]
#     print('{: >30} {: >10} {: >10} {: >10} {: >10} {: >10} {: >10}'.format(*row))

# plt.figure(figsize=(25, 15))
# plt.boxplot(results, labels=regressors.keys(), showmeans=True)
# plt.show()
# %% Submission
y_pred_test = test_predictions.mean(axis=1).round().astype(int)
# remap predictions to original scale
y_pred_test += min_y

sub = pd.read_csv('submissions/sample_submission.csv')
sub['quality'] = y_pred_test
now = time.strftime("%Y-%m-%d %H_%M_%S")
sub.to_csv(f'submissions/submission{now}.csv', index=False)
# %%
