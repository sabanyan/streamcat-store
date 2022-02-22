
def copy_nm(nysol_module, number):
    """
    指定したnysol_moduleを
    指定した数だけコピーして返す

    使い方の一例
    ・2つにコピー
    [f, f1] = copy_nm(nysol_module, 2)

    ・10個にコピー
    [f, f1, f2, f3, f4, f5, f6, f7, f8, f9] = copy_nm(nysol_module, 10)
    """

    module_list = []
    for i in range(0, number):
        f = None
        f <<= nysol_module
        module_list.append(f)
    return module_list
