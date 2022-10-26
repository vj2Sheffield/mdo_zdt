
import pandas as pd
import open_mdo as mdo


def read_value(zdt_n, n_d, n_y_vec, n_x_vec, structure):

    filename = 'results/ZDT' + str(zdt_n) + '/' + str(structure) + '/D' + str(n_d) + '/cases_var_params.sql'
    cr = mdo.om.CaseReader(filename)
    # cr = mdo.om.CaseReader('cases_var_params.sql')
    driver_cases = cr.get_cases('driver', recurse=False)  # List driver cases (do not recurse to system/solver cases)
    solver_cases = cr.list_cases('root.cycle.nonlinear_solver', out_stream=None)

    p = 0
    y_data = []
    xhat_data = []
    for case_id in solver_cases:
        case = cr.get_case(case_id)
        yvd = {}
        for i in range(1, n_d + 1):
            yvector = case['y' + str(i)]
            p = p + 1
            for j in range(n_y_vec[i - 1]):
                yvd['y' + str(i) + str(j + 1)] = yvector[j][0]
        y_data.append(yvd)

        xhatvd = {}
        for i in range(1, n_d + 1):
            xhatvector = case['xhat_' + str(i)]
            for j in range(n_x_vec[i - 1]):
                xhatvd['xhat_' + str(i) + str(j + 1)] = xhatvector[j][0]
        xhat_data.append(xhatvd)

    y_df = pd.DataFrame(data=y_data)
    xhat_df = pd.DataFrame(data=xhat_data)

    results_df = y_df.join(xhat_df)

    return results_df


if __name__ == '__main__':

    seed = 1
    zdt_n = 4
    n_d = 3
    n_y_vec = [5, 5, 5]
    n_x_vec = [5, 5, 5]
    topology = 1

    if topology == 1:
        structure = 'OIOO'
    elif topology == 2:
        structure = 'TITO'
    else:
        structure = 'AIAO'

    df = read_value(zdt_n, n_d, n_y_vec, n_x_vec, structure)

    filename_save = 'results/ZDT' + str(zdt_n) + '/' + str(structure) + '/D' + str(n_d) + \
                    ' /all_pop_y_xhat_zdt' + str(zdt_n) + '_nsub_' + str(n_d) + '_seed_' + str(seed) + '.csv'
    df.to_csv(filename_save, index=False)
