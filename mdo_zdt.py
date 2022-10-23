import os.path
import sys
import random
import json

import numpy as np
import pandas as pd

import open_mdo as mdo
from zdt import ZDT


def generate_row_norm_matrix(n_rows, n_cols):
    mat = np.random.rand(n_rows, n_cols)
    row_sums = mat.sum(axis=1)
    mat_norm = mat / row_sums[:, np.newaxis]
    return mat_norm


def generate_global_variable_matrices(_n_y_vec, _n_z=10):
    c_list = [generate_row_norm_matrix(n_y, _n_z - 1) for n_y in _n_y_vec]
    return c_list


def generate_local_variable_matrices(_n_y_vec, _n_x_vec):
    if len(_n_y_vec) != len(_n_x_vec):
        raise Exception("The vectors n_y and n_x need to have the same size.")
    d_list = [generate_row_norm_matrix(n_y, n_x) for (n_y, n_x) in zip(_n_y_vec, _n_x_vec)]
    return d_list


def generate_linking_variable_matrices(_n_y_vec, _p_vec, scaler=1):
    if len(_n_y_vec) != len(_p_vec):
        raise Exception("The vectors n_y and p need to have the same size.")
    b_all = []
    for (n_y, pi) in zip(_n_y_vec, _p_vec):
        b_list = [scaler*generate_row_norm_matrix(n_y, _n_y_vec[p-1]) for p in pi]
        b_all.append(b_list)
    return b_all


class MDO_ZDT:

    def __init__(self):

        self.nGen = 2
        self.popsize = 100

        self.zdt_number = 1
        self.n_z = 10
        self.n_x_vec = [5, 5, 5]
        self.n_y_vec = [5, 5, 5]
        self.p_vec = [[3], [1], [2]]  # OIOO
        self.bMatrix_scaler = 2

    @property
    def number_disciplines(self):
        return len(self.n_x_vec)

    def load_parameters(self, _filename):
        with open(_filename) as f:
            variables = json.load(f)
        for key, value in variables.items():
            setattr(self, key, value)

    def run(self, _seed):
        n_disciplines = self.number_disciplines

        # ZDT problem parameters
        zdt_prob = ZDT()
        zdt_prob.zdt_number = self.zdt_number
        zdt_prob.number_global_variables = self.n_z
        zdt_prob.number_local_variables_per_discipline = self.n_x_vec

        # obtained from the test problem
        z_lower = np.array(zdt_prob.global_variables_lower_bounds())
        z_upper = np.array(zdt_prob.global_variables_upper_bounds())
        x_lower_bounds = zdt_prob.local_variables_lower_bounds()
        x_upper_bounds = zdt_prob.local_variables_upper_bounds()

        b_list = generate_linking_variable_matrices(self.n_y_vec, self.p_vec, self.bMatrix_scaler)
        c_list = generate_global_variable_matrices(self.n_y_vec, self.n_z)
        d_list = generate_local_variable_matrices(self.n_y_vec, self.n_x_vec)

        kwargs = {'n_sub': n_disciplines,
                  'z_dummy': np.zeros((self.n_z, 1)),
                  'z_initial': np.array(random.sample(range(100), self.n_z)) / 100}
        for i in range(1, n_disciplines + 1):
            n_x = self.n_x_vec[i - 1]
            # local variables
            kwargs['x' + str(i) + '_dummy'] = np.ones((n_x, 1))
            kwargs['x' + str(i) + '_initial'] = np.array(random.sample(range(100), n_x)) / 100
            # linking variables
            kwargs['p' + str(i)] = self.p_vec[i - 1]
            kwargs['y' + str(i)] = np.ones((self.n_y_vec[i - 1], 1))
            kwargs['y' + str(i) + '_star'] = np.zeros((self.n_y_vec[i - 1], 1))
            # matrices
            for (j, bmatrix) in zip(self.p_vec[i - 1], b_list[i - 1]):
                kwargs['B' + str(i) + str(j)] = bmatrix
            kwargs['C' + str(i)] = c_list[i - 1]
            kwargs['D' + str(i)] = d_list[i - 1]

        f1_expr, f2_expr = zdt_prob.to_string()
        kwargs['f1_expr'] = f1_expr
        kwargs['f2_expr'] = f2_expr

        model = mdo.MDA(**kwargs)
        prob = mdo.om.Problem(model=model)

        prob.driver = mdo.om.pyOptSparseDriver(optimizer='NSGA2')
        prob.driver.opt_settings["maxGen"] = self.nGen
        prob.driver.opt_settings["PopSize"] = self.popsize
        prob.driver.opt_settings["seed"] = float(_seed / 10.0)
        prob.driver.opt_settings["pCross_real"] = 0.9
        prob.driver.opt_settings["pMut_real"] = 1 / (self.n_z + sum(self.n_x_vec))
        prob.driver.opt_settings["eta_c"] = 20.0
        prob.driver.opt_settings["eta_m"] = 20.0

        # Add design variables
        model.add_design_var("z", lower=z_lower, upper=z_upper)
        for i in range(1, n_disciplines + 1):
            model.add_design_var('x' + str(i), lower=x_lower_bounds[i - 1], upper=x_upper_bounds[i - 1])

        # Add objective
        model.add_objective("f1")
        model.add_objective("f2")

        recorder = mdo.om.SqliteRecorder('cases_var_params.sql')
        prob.add_recorder(recorder)  # Attach recorder to the problem
        prob.driver.add_recorder(recorder)  # Attach recorder to the driver
        prob.setup()

        model.obj2.add_recorder(recorder)  # Attach recorder to a subsystem
        model.cycle.nonlinear_solver.add_recorder(recorder)

        prob.set_solver_print(level=0)
        prob.run_driver()
        prob.run_model()
        prob.record("final_state")
        prob.cleanup()

        # Instantiate your CaseReader
        cr = mdo.om.CaseReader("cases_var_params.sql")
        driver_cases = cr.get_cases('driver', recurse=False)  # List driver cases (do not recurse to system/solver cases)
        solver_cases = cr.list_cases('root.cycle.nonlinear_solver', out_stream=None)

        f1v = []
        f2v = []
        z_data = []
        x_data = []

        for case in driver_cases:
            f1v.append(case['obj1.f1'][0])
            f2v.append(case['obj2.f2'][0])
            zvd = {}
            for i in range(self.n_z):
                zvd['z' + str(i + 1)] = case['z'][i]
            z_data.append(zvd)
            xxdv = {}
            for i in range(1, n_disciplines + 1):
                xvector = case['x' + str(i)]
                for j in range(self.n_x_vec[i - 1]):
                    xxdv['x' + str(i) + str(j + 1)] = xvector[j]
            x_data.append(xxdv)

        obj_data = {'f1': f1v, 'f2': f2v}
        obj_df = pd.DataFrame(data=obj_data)
        z_df = pd.DataFrame(data=z_data)
        x_df = pd.DataFrame(data=x_data)

        y_data = []
        xhat_data = []
        for case_id in solver_cases:
            case = cr.get_case(case_id)
            yvd = {}
            for i in range(1, n_disciplines + 1):
                yvector = case['y' + str(i)]
                for j in range(self.n_y_vec[i - 1]):
                    yvd['y' + str(i) + str(j + 1)] = yvector[j][0]
            y_data.append(yvd)

            xhatvd = {}
            for i in range(1, n_disciplines + 1):
                xhatvector = case['xhat_' + str(i)]
                for j in range(self.n_x_vec[i - 1]):
                    xhatvd['xhat_' + str(i) + str(j + 1)] = xhatvector[j][0]
            xhat_data.append(xhatvd)

        y_df = pd.DataFrame(data=y_data)
        xhat_df = pd.DataFrame(data=xhat_data)

        all_df = obj_df.join(z_df.join(x_df.join(y_df.join(xhat_df))))

        return all_df


if __name__ == '__main__':

    seed = int(sys.argv[1])
    filename = sys.argv[2]

    mdo_obj = MDO_ZDT()
    if os.path.isfile(filename):
        mdo_obj.load_parameters(filename)

    popsize = mdo_obj.popsize
    zdt_n = mdo_obj.zdt_number
    n_d = mdo_obj.number_disciplines

    np.random.seed(seed)
    results_df = mdo_obj.run(seed)
    last_pop_df = results_df.iloc[-popsize:]

    last_pop_df.to_csv('last_pop_zdt' + str(zdt_n) + '_nsub_' + str(n_d) + '_seed_' + str(seed) + '.csv', index=False)
    results_df.to_csv('all_pop_zdt' + str(zdt_n) + '_nsub_' + str(n_d) + '_seed_' + str(seed) + '.csv', index=False)
