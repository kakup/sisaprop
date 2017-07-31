from collections import namedtuple
ApropDataRow = namedtuple("ApropDataRow",
                          ('matr_func', 'nome_func', 'apelido', 'nome_apropriador', 'matr_apropriador',
                          'nome_setor', 'nome_planilha', 'turno', 'suplentes', 'flags'))