
import numpy as np
import openmdao.api as om


class Subsystem(om.ExplicitComponent):

    def __init__(self, **kwargs):

        self.d_n = kwargs['d_n']  # subsystem number
        self.z_dummy = kwargs['z_dummy']
        self.xi_dummy = kwargs['x' + str(self.d_n) + '_dummy']

        self.pi = kwargs['p' + str(self.d_n)]
        self.y_dummy_dic = {'y' + str(self.d_n): kwargs['y' + str(self.d_n)]}
        self.y_star_dic = {'y' + str(self.d_n) + '_star': kwargs['y' + str(self.d_n) + '_star']}
        self.bi_dic = {}
        for j in self.pi:
            dic_key = 'y' + str(j)
            self.y_dummy_dic[dic_key] = kwargs[dic_key]
            self.y_star_dic[dic_key + '_star'] = kwargs[dic_key + '_star']
            self.bi_dic['B' + str(self.d_n) + str(j)] = kwargs['B' + str(self.d_n) + str(j)]

        self.ci = kwargs['C' + str(self.d_n)]
        self.di = kwargs['D' + str(self.d_n)]

        super().__init__()

    def setup(self):

        self.add_input('z', val=self.z_dummy)
        self.add_input('x' + str(self.d_n), val=self.xi_dummy)
        for i in self.pi:
            dic_key = 'y' + str(i)
            self.add_input(dic_key, val=self.y_dummy_dic[dic_key])

        dic_key = 'y' + str(self.d_n)
        self.add_output(dic_key, val=self.y_dummy_dic[dic_key])
        self.add_output('xhat_' + str(self.d_n), val=self.xi_dummy)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        z = inputs["z"]
        xi = inputs['x' + str(self.d_n)]

        cz = np.matmul(self.ci, z[1:])
        dx = np.matmul(self.di, xi)
        y_output = -cz - dx

        for i in self.pi:
            y = inputs['y' + str(i)]
            b = self.bi_dic['B' + str(self.d_n) + str(i)]
            by = np.matmul(b, y)
            y_output += by

        outputs['y' + str(self.d_n)] = y_output
        y_star = self.y_star_dic['y' + str(self.d_n) + '_star']
        diff = abs(y_output - y_star)
        res = xi + diff
        outputs['xhat_' + str(self.d_n)] = res


class MDA(om.Group):

    def __init__(self, **kwargs):

        self.n_sub = kwargs['n_sub']  # number of subsystems

        # global variables
        self.z_dummy = kwargs['z_dummy']
        self.z_initial = kwargs['z_initial']

        # local variables
        self.x_dummy_dic = {}
        self.x_initial_dic = {}
        for i in range(1, self.n_sub+1):
            self.x_dummy_dic['x' + str(i)] = kwargs['x' + str(i) + '_dummy']
            self.x_initial_dic['x' + str(i)] = kwargs['x' + str(i) + '_initial']

        # linking variables
        self.p_dic = {}
        for i in range(1, self.n_sub + 1):
            self.p_dic['p' + str(i)] = kwargs['p' + str(i)]
        self.y_dic = {}
        for i in range(1, self.n_sub + 1):
            self.y_dic['y' + str(i)] = kwargs['y' + str(i)]
        self.y_star_dic = {}
        for i in range(1, self.n_sub + 1):
            self.y_star_dic['y' + str(i)] = kwargs['y' + str(i) + '_star']

        # matrices
        self.bi_dic = {}
        for i in range(1, self.n_sub + 1):
            for j in self.p_dic['p' + str(i)]:
                self.bi_dic['B' + str(i) + str(j)] = kwargs['B' + str(i) + str(j)]

        self.ci_dic = {}
        for i in range(1, self.n_sub + 1):
            self.ci_dic['C' + str(i)] = kwargs['C' + str(i)]

        self.di_dic = {}
        for i in range(1, self.n_sub + 1):
            self.di_dic['D' + str(i)] = kwargs['D' + str(i)]

        # ZDT problem function expressions
        self.f1_expr = kwargs['f1_expr']
        self.f2_expr = kwargs['f2_expr']

        super().__init__()

    def setup(self):
        cycle = self.add_subsystem("cycle", om.Group(), promotes=["*"])
        for i in range(1, self.n_sub+1):

            skwargs = {'d_n': i,
                       'z_dummy': self.z_dummy,
                       'x' + str(i) + '_dummy': self.x_dummy_dic['x' + str(i)],
                       'p' + str(i): self.p_dic['p' + str(i)],
                       'y' + str(i): self.y_dic['y' + str(i)],
                       'y' + str(i) + '_star': self.y_star_dic['y' + str(i)]}

            for j in self.p_dic['p' + str(i)]:
                skwargs['y' + str(j)] = self.y_dic['y' + str(j)]
                skwargs['y' + str(j) + '_star'] = self.y_star_dic['y' + str(j)]
                skwargs['B' + str(i) + str(j)] = self.bi_dic['B' + str(i) + str(j)]

            skwargs['C' + str(i)] = self.ci_dic['C' + str(i)]
            skwargs['D' + str(i)] = self.di_dic['D' + str(i)]

            s_obj = Subsystem(**skwargs)

            p_inputs = ['z', 'x' + str(i)]
            for j in self.p_dic['p' + str(i)]:
                p_inputs.append('y' + str(j))
            p_outputs = ['y' + str(i), 'xhat_' + str(i)]

            cycle.add_subsystem('d'+str(i), s_obj, promotes_inputs=p_inputs, promotes_outputs=p_outputs)

            cycle.set_input_defaults('x' + str(i), self.x_initial_dic['x' + str(i)])
        cycle.set_input_defaults('z', self.z_initial)

        promotes_f2 = ['z', 'f2']
        for i in range(1, self.n_sub + 1):
            promotes_f2.append('xhat_' + str(i))

        self.add_subsystem("obj1", om.ExecComp('f1 = ' + self.f1_expr, z=self.z_dummy), promotes=["z", "f1"])

        f2_kwargs = {'z': self.z_dummy}
        for i in range(1, self.n_sub + 1):
            f2_kwargs['xhat_' + str(i)] = self.x_dummy_dic['x' + str(i)]
        self.add_subsystem("obj2", om.ExecComp(exprs='f2 = ' + self.f2_expr, **f2_kwargs), promotes=promotes_f2)

        cycle.nonlinear_solver = om.NewtonSolver(maxiter=1000, solve_subsystems=True)
        cycle.linear_solver = om.DirectSolver()
