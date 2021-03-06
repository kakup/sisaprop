__author__ = 'carlos.coelho'

import re

import logging
import os
import zipfile

from .autoapropxlsx.autoapropmaptypes import AutoApropModeloSemanal, AutoApropModeloDiario, \
    AutoApropModeloDiarioAdministrativo, AutoApropException

from sisaprop.map.map import Map
from .maprendererbase import MapRendererBase


l = logging.getLogger("AutoApropXlsxMapRenderer")

class AutoApropXlsxMapRenderer(MapRendererBase):
    def realrender(self, _map: Map, _path):

        l.debug("Map is [{0}]".format(_map))
        l.debug("RenderPath is [{0}]".format(_path))

        # Split maps by "nome_planilha"
        submaps = _map.getsplitmapdata(keysorting='nome_planilha')

        # Dumplist
        self.dumplist = []

        l.debug("{0} submap(s) to render from map...".format(len(submaps)))
        for submapname in submaps:
            rendersubmapname = submapname.split(u'/')[-1].lower()
            assert isinstance(rendersubmapname, str)
            rendersubmapname = rendersubmapname.replace(u'.',u'') + u'.xlsx'
            rendersubmapname = self.fix_nomeplanilha(rendersubmapname)

            # Get filename from rendersubmapname
            renderfilename = os.path.join(_path, rendersubmapname.upper())

            # Generate each map.
            print("  Renderizando mapa {0} ({1})...".format(submapname, rendersubmapname))
            l.debug("Rendering submap \"{0}\".".format(submapname))
            self.rendereachmap(submaps[submapname], rendersubmapname, renderfilename)
            l.debug(" ")

        l.info("Generating dump list...")
        self.generate_dumplist(_path)

    @staticmethod
    def fix_nomeplanilha(nomeplanilha: str):
        # Strip unwanted characters
        n = re.sub(r'\*', '', nomeplanilha)
        n = re.sub(r'!', '', n)
        return n

    def rendereachmap(self, _map : Map, _mapname, _renderfilepath):
        assert isinstance(_map, Map)

        bigemployeelist = _map.get_all_funcionarios()

        for slice in bigemployeelist:
            employees, params = tuple(slice)
            apropriador_com_matr, nome_setor, nome_planilha_orig, turno = params

            # Fix nome_planilha if it has some flags ('*' = administrativo)
            nome_planilha = self.fix_nomeplanilha(nome_planilha_orig)

            nome_apropriador, matr_apropriador = apropriador_com_matr

            l.debug("    [slice] > {0:s} {1:s} {2:s}".format(nome_apropriador, nome_setor, turno))

            # Build Dict for renderer
            renderdict = {}

            renderdict["##NOMESETOR##"]  = nome_setor
            renderdict["##NOMEPLANILHA##"] = nome_planilha

            renderdict["##NOMERESP##"] = nome_apropriador
            renderdict["##MATRRESP##"] = matr_apropriador

            renderdict["##EMPCOUNT##"] = len(employees)

            for emp, empcount in zip(employees, range(1,len(employees)+1)):
                _empmatr, _nome, _apelido, _flags = emp

                # Nome OR Apelido
                _empnome = _apelido if _apelido else _nome

                renderdict["##NOME{}##".format(empcount)] = _empnome
                renderdict["##MATR{}##".format(empcount)] = _empmatr

                # Populate Dumplist
                self.dumplist.append(
                    (nome_setor.replace('\r\n','--'), nome_planilha, nome_apropriador,
                     matr_apropriador, _empmatr, _nome, _apelido, _flags)
                )

            # Get submap_flags for this submap
            submap_flags = _map.get_flags_for(nome_planilha=nome_planilha_orig)

            # Choose model from employeecount and from submap_flags
            xlsxtemplate = AutoApropModeloSemanal

            if "diario" in submap_flags:
                xlsxtemplate = AutoApropModeloDiario
            elif len(employees) > 6:
                # If we want administrativo-only template
                if "administrativo" in submap_flags:
                    xlsxtemplate = AutoApropModeloDiarioAdministrativo
                else:
                    xlsxtemplate = AutoApropModeloDiario

            try:
                # Render
                xlsxtemplate.render(_renderdict=renderdict, _outputxlsxpath=_renderfilepath)
            except AutoApropException as e:
                l.error("Erro renderizando XLSX[{}]: Pulando render de {}".format(xlsxtemplate, _renderfilepath))
                print(e)

    def generate_dumplist(self, _path: str):
        renderfilename = os.path.join(_path, "dumplist.txt")
        f = open(renderfilename, 'w')

        emplist = sorted([str(x) for x in self.dumplist])

        f.write('\n'.join(emplist))

