import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# Generate synthetic data
np.random.seed(42)
n_samples = 1000
X = np.random.rand(n_samples, 3)
X[:, 2] = np.random.binomial(1, 0.5, n_samples)

# Create target with a known relationship
prob = 1 / (1 + np.exp(-(2*X[:,0] + 3*X[:,1] + 1*X[:,2])))
y = (np.random.rand(n_samples) < prob).astype(int)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Fit logistic regression
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Show coefficients
print('Coefficients:', model.coef_)
print('Intercept:', model.intercept_)