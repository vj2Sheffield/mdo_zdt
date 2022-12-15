# mdo_zdt #

## Description ##

MDO-ZDT allows users to generate and evaluate the ZDT problems applied within a multidisciplinary design optimisation (MDO) framework. It is written in Python using the OpenMDAO [1] and PyOptSparse [2] packages developed by the MDO Lab at the University of Michigan.

Each of the MDO-ZDT problems can be configured with varying numbers of disciplines, global, local and linking variables, as well as different inter-disciplinary relationships. 

# Requirements #

- Python 
- OpenMDAO
- PyOptSparse 2.8.3
- numpy and pandas

# Installation #

The repository must be cloned from github and used locally.

# Quickstart #

To run the generator, use the following code:

> python mdo-zdt.py SEED FILENAME

where SEED is the seed for the random number generator and must be an integer greater than 0 and less than 100, and FILENAME is the name of the .json file that contains the parameters defining the structure of the MDO system. These files include:

- number of generations nGen
- size of population popSize
- ZDT number zdt_number
- number of global variables n_z
- number of local variables in each discipline n_x_vec
- number of linking variables in each discipline n_y_vec
- inter-disciplinary relationships (known as p-vector) p_vec
- scaler for the B matrices in the multidisciplinary analyses (this is usually either 1 or 2) bMatrix_scaler

A number of pre-set parameter files can be found in the /parameters folder, but you can also create new ones as needed. The corresponding linking and local vectors must be the same for proper operation - for example, n_x_vec[i] = n_y_vec[i].

# References #

[1] J. S. Gray, J. T. Hwang, J. R. R. A. Martins, K. T. Moore, and B. A. Naylor, “OpenMDAO: An Open-Source Framework for Multidisciplinary Design, Analysis, and Optimization,” Structural and Multidisciplinary Optimization, vol. 59, no. 4, pp. 1075–1104, 2019, doi: 10.1007/s00158-019-02211-z.

[2] N. Wu, G. Kenway, C. A. Mader, J. Jasa, and J. R. R. A. Martins. pyOptSparse: A Python framework for large-scale constrained nonlinear optimization of sparse systems. Journal of Open Source Software, 5(54), 2564, October 2020. https://doi.org/10.21105/joss.02564.