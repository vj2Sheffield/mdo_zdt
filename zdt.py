
class ZDT:

    ZDT_CATEGORIES = {1, 2, 3, 4, 6}

    def __init__(self):
        self._zdt = 1  # ZDT problem number
        self._n_gvar = 10  # number of global variables
        self._n_lvar = [5, 5, 5]  # number of local variables per discipline

        # calculate dependent variables
        self._calculate_dependent_variables()

    def _calculate_dependent_variables(self):
        self._n_d = len(self._n_lvar)  # number of disciplines
        self._nv = self._n_gvar + sum(self._n_lvar)
        self._nVar = self._nv - 1
        self._nVar_str = str(self._nVar)

    @property
    def zdt_number(self):
        return self._zdt

    @zdt_number.setter
    def zdt_number(self, a):
        if a not in self.ZDT_CATEGORIES:
            raise ValueError("{} is not a supported ZDT problem number".format(a))
        self._zdt = a

    @property
    def number_global_variables(self):
        return self._n_gvar

    @number_global_variables.setter
    def number_global_variables(self, a):
        if a < 1:
            raise ValueError("The number of global variables need to be higher than zero")
        self._n_gvar = a
        self._calculate_dependent_variables()

    @property
    def number_local_variables_per_discipline(self):
        return self._n_lvar

    @number_local_variables_per_discipline.setter
    def number_local_variables_per_discipline(self, a):
        if len(a) < 1:
            raise ValueError("The number of disciplines needs to be higher than zero")
        for nvar in a:
            if nvar < 1:
                raise ValueError("Each discipline needs to have at least one local variable")
        self._n_lvar = a
        self._calculate_dependent_variables()

    @property
    def number_disciplines(self):
        return self._n_d

    def global_variables_lower_bounds(self):
        if self._zdt == 4:
            res = [-5.0] * self._n_gvar
            res[0] = 0.0
            return res
        else:
            return [0.0] * self._n_gvar

    def global_variables_upper_bounds(self):
        if self._zdt == 4:
            res = [5.0] * self._n_gvar
            res[0] = 1.0
            return res
        else:
            return [1.0] * self._n_gvar

    def local_variables_lower_bounds(self):
        if self._zdt == 4:
            return [[-5.0] * s for s in self._n_lvar]
        else:
            return [[0.0] * s for s in self._n_lvar]

    def local_variables_upper_bounds(self):
        if self._zdt == 4:
            return [[5.0] * s for s in self._n_lvar]
        else:
            return [[1.0] * s for s in self._n_lvar]

    def to_string(self):
        temp_old = ''
        f1 = ''

        g = ''
        # ZDT1, 2, 3
        if self._zdt == 1 or self._zdt == 2 or self._zdt == 3:
            for m in range(1, self._n_d):
                temp = 'sum(xhat_' + str(m) + ') + '
                temp_old = temp_old + temp
            temp_old = temp_old + 'sum(xhat_' + str(self._n_d) + ') + sum(z[1:' + str(self._n_gvar) + '])'
            g = '(1 + (9/' + self._nVar_str + ')*(' + temp_old + '))'
            f1 = 'z[0]'

        # ZDT4
        if self._zdt == 4:
            for m in range(1, self._n_d):
                temp = 'sum(xhat_' + str(m) + '**2 - 10*cos(4*pi*xhat_' + str(m) + ')) + '
                temp_old = temp_old + temp

            temp_old = temp_old + 'sum(xhat_' + str(self._n_d) + '**2 - 10*cos(4*pi*xhat_' + str(self._n_d) + \
                       ')) + sum(z[1:' + str(self._n_gvar) + ']**2 - 10*cos(4*pi*z[1:' + str(self._n_gvar) + ']))'
            g = '(1 + 10*(' + self._nVar_str + ') + (' + temp_old + '))'
            f1 = 'z[0]'

        # ZDT6
        if self._zdt == 6:
            for m in range(1, self._n_d):
                temp = 'sum(xhat_' + str(m) + ') + '
                temp_old = temp_old + temp

            temp_old = temp_old + 'sum(xhat_' + str(self._n_d) + ') + sum(z[1:' + str(self._n_gvar) + '])'
            g = '(1 + 9*((' + temp_old + ')/9)**0.25)'
            f1 = '(1 - exp(-4*z[0])*sin(6*pi*z[0])**6)'

        h = ''
        # ZDT1 or ZDT4
        if self._zdt == 1 or self._zdt == 4:
            h = '(1 - (' + f1 + '/' + g + ')**0.5)'

        # ZDT2 or ZDT6
        if self._zdt == 2 or self._zdt == 6:
            h = '(1 - (' + f1 + '/' + g + ')**2)'

        # ZDT3
        if self._zdt == 3:
            h = '(1 - (' + f1 + '/' + g + ')**0.5 - (' + f1 + '/' + g + ')*sin(10*pi*' + f1 + '))'

        f2 = g + '*' + h

        return f1, f2


if __name__ == '__main__':

    zdt_obj = ZDT()

    print(zdt_obj.to_string())

    zdt_obj.zdt_number = 6
    zdt_obj.number_global_variables = 10
    zdt_obj.number_local_variables_per_discipline = [5, 5, 5]

    print(zdt_obj.to_string())
