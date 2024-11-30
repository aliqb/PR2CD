import numpy as np

# Step 1: Define the pairwise comparison matrices
# Example: 5 matrices from 5 people
# Matrix format: M[i][j] = comparison between criteria i and j

# Example pairwise matrices (corrected)
M1 = np.array([[1, 5, 5, 1 / 5],
               [1 / 5, 1, 1 / 8, 1 / 3],
               [1 / 5, 8, 1, 1 / 9],
               [5, 3, 9, 1]])

M2 = np.array([[1, 9, 7, 7],
               [1 / 9, 1, 3, 1 / 2],
               [1 / 7, 1 / 3, 1, 1 / 3],
               [1 / 7, 2, 3, 1]])

M3 = np.array([[1, 5, 5, 5],
               [1 / 5, 1, 2, 1 / 3],
               [1 / 5, 1 / 2, 1, 1 / 2],
               [1 / 5, 3, 2, 1]])

M4 = np.array([[1, 7, 6, 6],
               [1 / 7, 1, 3, 1 / 4],
               [1 / 6, 1 / 3, 1, 1 / 4],
               [1 / 6, 4, 4, 1]])

M5 = np.array([[1, 3, 3, 1 / 5],
               [1 / 3, 1, 1 / 8, 1 / 6],
               [1 / 3, 8, 1, 5],
               [5, 6, 1 / 5, 1]])

# Step 2: Average the matrices
matrices = [M1, M2, M3, M4, M5]

# Sum corresponding elements from each matrix and divide by the number of matrices (5)
average_matrix = np.mean(matrices, axis=0)

# Step 3: Normalize the average matrix (normalize columns)
# Sum each column
column_sums = np.sum(average_matrix, axis=0)

# Normalize each element by dividing by the column sum
normalized_matrix = average_matrix / column_sums

# Step 4: Calculate the weights (average of rows of the normalized matrix)
weights = np.mean(normalized_matrix, axis=1)

# Step 5: Display the results
print("Average Matrix:\n", average_matrix)
print("\nNormalized Matrix:\n", normalized_matrix)
print("\nWeights (Criteria Importance):", weights)