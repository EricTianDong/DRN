
import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
from typing import Callable, Optional
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt


from tqdm.auto import trange, tqdm
from typing import List, Union

import torch
import torch.nn as nn
from torch.distributions import Categorical, Distribution, constraints
from torch.distributions.mixture_same_family import MixtureSameFamily

import re

import sklearn
import scipy
import statsmodels.api as sm
from scipy.ndimage import gaussian_filter1d
from scipy.integrate import quad
from scipy.stats import norm

from .histogram_class import Histogram

class DDR(nn.Module):
    def __init__(self, p: int, cutpoints, num_hidden_layers=2, hidden_size=100, dropout_rate = 0.2):
        """
        Args:
            x_train_shape: The shape of the training data, used to define the input size of the first layer.
            cutpoints: The cutpoints for the DDR model.
            num_hidden_layers: The number of hidden layers in the network.
            hidden_size: The number of neurons in each hidden layer.
        """
        super(DDR, self).__init__()
        self.cutpoints = nn.Parameter(torch.Tensor(cutpoints), requires_grad=False)
        self.p = p

        layers = [nn.Linear(self.p, hidden_size), nn.ReLU(), nn.Dropout(dropout_rate)]
        for _ in range(num_hidden_layers - 1):
            layers.append(nn.Linear(hidden_size, hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_rate)) 

        # Use nn.Sequential to chain the layers together
        self.hidden_layers = nn.Sequential(*layers)
        
        # Output layer for the pi values
        self.pi = nn.Linear(hidden_size, len(self.cutpoints) - 1)

    def forward(self, x):
        """
        Forward pass of the DDR model.
        Args:
            x: Input tensor.
        Returns:
            The cutpoints and probabilities for the DDR model.
        """
        # Pass input through the dynamically created hidden layers
        h = self.hidden_layers(x)
        
        # Calculate probabilities using the final layer
        probs = torch.softmax(self.pi(h), dim=1)
        
        return self.cutpoints, probs

    def distributions(self, x):
        cutpoints, prob_masses = self.forward(x)
        dists = Histogram(cutpoints, prob_masses)
        assert dists.batch_shape == torch.Size([x.shape[0]])
        return dists