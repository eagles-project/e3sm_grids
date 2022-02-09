import xarray as xr
from glob import glob
import warnings
import re
from collections import namedtuple
from bashparser import BashParser

def verbose_print(msg, verbose=True):
    """print msg if verbose is True (do nothing if False)"""
    if verbose:
        print(msg)

class RRMHelper:
    Links = namedtuple('Links', ['script', 'files', 'gen_func', 'kwargs'],
                       defaults=[None, None, None, None])
    
    def __repr__(self):
        return f'RRMHelper({self.script_dir}, {self.config_script})'
    
    def __init__(self, script_dir='', config_script='config.sh'):
        self.script_dir = script_dir
        self.config_script = config_script
        self.variables = BashParser(f'{script_dir}/{config_script}').parse()
        self.mesh_files = self._gen_mesh_files()
        self.map_files = self._gen_map_files()
        self.domain_files = self._gen_domain_files()
        self.topography_file = self._gen_topography_file()
        self.dry_deposition_file = self._gen_dry_deposition_file()
        self.dry_deposition_aux_files = self._gen_dry_deposition_aux_files()
        self.topography_aux_files = self._gen_topography_aux_files()
        self.atm_ic = self._gen_atm_ic()
        self.output = self.check_output()
        self._links = {'mesh': RRMHelper.Links('generate_initial_mesh.sh', self.mesh_files, self._gen_mesh_files),
                       'map': RRMHelper.Links('generate_mapping_files.sh', self.map_files, self._gen_map_files, ['date']),
                       'domain': RRMHelper.Links('generate_domain_files.sh', self.domain_files, self._gen_domain_files, ['date']),
                       'topo': RRMHelper.Links('generate_topo.sh', self.topography_file, self._gen_topography_file),
                       'dry_dep': RRMHelper.Links('generate_atmsrf.sh', self.dry_deposition_file, self._gen_dry_deposition_file, ['date']),
                       'topo_aux': RRMHelper.Links('generate_topo.sh', self.topography_aux_files, self._gen_topography_aux_files),
                       'dry_dep_aux': RRMHelper.Links('generate_atmsrf.sh', self.dry_deposition_aux_files, self._gen_dry_deposition_aux_files, ['date']),
                       'atm_ic': RRMHelper.Links('create_atm_initial_condition.sh', self.atm_ic, self._gen_atm_ic, ['ic_date'])}
        self.dependencies = {'mesh': None,
                             'map': 'mesh',
                             'domain': ('mesh', 'map'),
                             'topo': 'mesh',
                             'dry_dep': 'mesh',
                             'topo_aux': 'mesh',
                             'dry_dep_aux': 'mesh',
                             'atm_ic': ('mesh', 'topo')}
    
    def get_runscript(self, name):
        return f'{self.script_dir}/{self._links[name].script}'
        
    def check_output(self, verbose=False):
        # use get method to gracefully fail if output_root doesn't exist
        output_contents = glob(f'{self.variables.get("output_root")}/*')
        if verbose:
            print(f'Contents of output directory {self.variables.get("output_root")}:')
            print(*sorted(output_contents), sep='\n')
        return output_contents
    
    def update_output(self, verbose=False):
        self.output = self.check_output(verbose=verbose)
        
    def _check_for_alternate_date(self, link, date_match='latest', verbose=False):
        """Use link info to check if other file exists with alternate date"""
        if not link.kwargs:
            print(f'No kwargs for {link.gen_func}')
            return link.files
        # check for alternate dates by inserting '!':
        kwargs = {key: '!' for key in link.kwargs}
        test_files = link.gen_func(**kwargs)  # this is a dictionary
        # strip off date
        pos_dict = {key: test.find('!') for key, test in test_files.items()}
        if verbose: print(pos_dict)
        
        # regex patterns should match yymmdd, yyyymmdd, yyyy-mm-dd, yy-mm-dd
        patterns = {key: f'{test_files[key][:pos]}[\d\-]*{test_files[key][pos+1:]}'
                    for key, pos in pos_dict.items()}
        if verbose: print('Patterns', patterns, sep='\n')
        matches = {key: self._search_path_for_alt_dates(patt) for key, patt in patterns.items()}
        if verbose: print('Matches', matches, sep='\n')
        if date_match == 'latest':
            if verbose: print(link.files)
            return {key: match[-1] if match else link.files[key] for key, match in matches.items()}
        else:
            return link.files
    
    def _search_path_for_alt_dates(self, pattern):
        matches = []
        for f in self.output:
            x = re.match(pattern, f)
            if x is not None:
                matches.append(x.group())
        return sorted(matches)
    
    def check_for_output_files(self, step, date_match='latest', update_output=False, verbose=True):
        links = self._links[step]
        verbose_print(step, verbose=verbose)
        if all(v in self.output for v in links.files.values()):
            # found!
            verbose_print(f'All {step} files found', verbose=verbose)
            return True
        else:
            if verbose:
                print(f'Some {step} files missing')
                for v in links.files.values():
                    print(v, v in self.output)
            if date_match == 'latest':
                verbose_print('Searching for other dates', verbose=verbose)
                out = self._check_for_alternate_date(links, date_match=date_match)
                if update_output:
                    verbose_print('Updating output files', verbose=verbose)
                    links.files.update(out)
                if all(v in self.output for v in out.values()):
                    verbose_print(f'All {step} files found with different dates', verbose=verbose)
                    return True
        return False
        
    def _locate_files(self, date_match='latest', update_output=False, verbose=True):
        """Check output directory to see if files exist"""
        kwargs = {'date_match': date_match, 'update_output': update_output, 'verbose': verbose}
        success = {key: self.check_for_output_files(key, **kwargs) for key in self._links}
        verbose_print(success, verbose=verbose)
        return success
            
        
    def _locate_files_orig(self, date_match='latest', update_output=False):
        """Check output directory to see if files exist"""
        for key, links in self._links.items():
            print(key)
            if all(v in self.output for v in links.files.values()):
                # found!
                print(f'All {key} files found')
            else:
                for v in links.files.values():
                    print(v, v in self.output)
                print(f'Some {key} files missing')
                if date_match == 'latest':
                    print('Searching for other dates')
                    out = self._check_for_alternate_date(links, date_match=date_match)
                    # print(out)
                    if all(v in self.output for v in out.values()):
                        print(f'All {key} files found with different dates')
                    if update_output:
                        print('Updating output files')
                        links.files.update(out)
    
    def _gen_mesh_files(self):
        return {'dyn_grid': f'{self.variables["output_root"]}/{self.variables["dyn_grid_name"]}.g',
                'atm_grid': f'{self.variables["output_root"]}/{self.variables["atm_grid_name"]}.g',
                'atm_scrip': f'{self.variables["output_root"]}/{self.variables["atm_grid_name"]}_scrip.nc'}

    def _gen_map_files(self, date=None):
        if date is None:
            date = self.variables['date']
        out_dir = self.variables['output_root']
        ocn = self.variables['ocn_grid_name']
        lnd = self.variables['lnd_grid_name']
        atm = self.variables['atm_grid_name']
        return {'map_ocn_to_lnd': f'{out_dir}/map_{ocn}_to_{lnd}_aave.{date}.nc',
                'map_ocn_to_atm': f'{out_dir}/map_{ocn}_to_{atm}_mono.{date}.nc',
                'map_atm_to_ocn': f'{out_dir}/map_{atm}_to_{ocn}_mono.{date}.nc',
                'map_lnd_to_atm': f'{out_dir}/map_{lnd}_to_{atm}_mono.{date}.nc',
                'map_atm_to_lnd': f'{out_dir}/map_{atm}_to_{lnd}_mono.{date}.nc',
                'map_ocn_to_lnd': f'{out_dir}/map_{ocn}_to_{lnd}_mono.{date}.nc',
                'map_atm_to_lnd_bilin': f'{out_dir}/map_{atm}_to_{lnd}_bilin.{date}.nc',
                'map_atm_to_ocn_bilin': f'{out_dir}/map_{atm}_to_{ocn}_bilin.{date}.nc',
                'map_ocn_to_lnd_nco': f'{out_dir}/map_{ocn}_to_{lnd}_nco.{date}.nc'}

    def _gen_domain_files(self, date=None):
        if date is None:
            date = self.variables['date']
        out_dir = self.variables['output_root']
        ocn = self.variables['ocn_grid_name']
        lnd = self.variables['lnd_grid_name']
        atm = self.variables['atm_grid_name']
        return {'ocn_domain_atm_ocn': f'{out_dir}/domain.ocn.{atm}_{ocn}.{date}.nc',
                'lnd_domain_atm_ocn': f'{out_dir}/domain.lnd.{atm}_{ocn}.{date}.nc',
                'ocn_domain_lnd_ocn': f'{out_dir}/domain.ocn.{lnd}_{ocn}.{date}.nc',
                'ocn_domain': f'{out_dir}/domain.ocn.{ocn}.{date}.nc',
                'lnd_domain_lnd_ocn': f'{out_dir}/domain.lnd.{lnd}_{ocn}.{date}.nc'}

    def _gen_topography_file(self):
        out_dir = self.variables['output_root']
        atm = self.variables['atm_grid_name']
        return {'topo': f'{out_dir}/USGS-gtopo30_{atm}_12xdel2.nc'}

    def _gen_topography_aux_files(self):
        out_dir = self.variables['output_root']
        dyn = self.variables['dyn_grid_name']
        atm = self.variables['atm_grid_name']
        return {'namelist': f'{out_dir}/homme_tool_input.nl',
                'pg4_grid': f'{out_dir}/{dyn}pg4.g',
                'pg4_scrip': f'{out_dir}/{dyn}pg4_scrip.nc',
                'pg4_topo': f'{out_dir}/{dyn}pg4_topo.nc',
                'smoothed_topo': f'{out_dir}/{atm}_smoothed_phis1.nc'}

    def _gen_dry_deposition_file(self, date=None):
        return {'atmsrf': f'{self.variables["output_root"]}/atmsrf_{self.variables["atm_grid_name"]}_{date}.nc'}

    def _gen_dry_deposition_aux_files(self, date=None):
        out_dir = self.variables['output_root']
        atm = self.variables['atm_grid_name']
        return {'map': f'{out_dir}/map_1x1_to_{atm}_mono.nc',
                'atmsrf_netcdf4': f'{out_dir}/atmsrf_{atm}_{date}_n4.nc'}

    def _gen_atm_ic(self, ic_date=None):
        """ic_date = YYYY-MM-DD for atm initial condition """
        return {'atm_ic': 'None' if ic_date is None else 
                f'{self.variables["output_root"]}/HICCUP.atm_era5.{ic_date}.{self.variables["atm_grid_name"]}.L72.nc'}
    
    def e3sm_config_edit_template(self, header=True, desc='1-deg with ne1024pg2 over ENA'):
        """Generate text blocks to copy/paste into relevant files"""        
        self._config_grids_txt(header=header, desc=desc)
        self._horz_grid_txt(header=header, ncol='infer')
        self._namelist_defaults_eam_txt(header=header)
        
    def get_ncol(self):
        if not hasattr(self, 'ncol'):
            try:
                ds_topo = xr.open_dataset(self.topography_file['topo'])
                self.ncol = ds_topo.dims['ncol']
            except:
                warnings.warn(f'Could not get ncol from {self.topography_file["topo"]}, setting to -1')
                self.ncol = -1
        return self.ncol

    def _print_filepath(self, relpath):
        filename = f'{self.variables["e3sm_root"]}/{relpath}'
        linebreak = '-' * len(filename)
        print(linebreak, filename, linebreak, sep='\n')
        
    def _config_grids_txt(self, header=True, desc='1-deg with ne1024pg2 over Eastern North Atlantic (version 0 test)'):
        if header:
            self._print_filepath('cime_config/config_grids.xml')
        
        atm_grid = self.variables['atm_grid_name']
        lnd_grid = self.variables['lnd_grid_name']
        ocn_grid = self.variables['ocn_grid_name']
        dyn_grid = self.variables['dyn_grid_name']
        
        model_grid = (f'    <model_grid alias="{atm_grid}_{lnd_grid}_{ocn_grid}">\n'
                      f'      <grid name="atm">ne0np4_{dyn_grid}.pg2</grid>\n'
                      f'      <grid name="lnd">{lnd_grid}</grid>\n'
                      f'      <grid name="ocnice">{ocn_grid}</grid>\n'
                      f'      <grid name="rof">{lnd_grid}</grid>\n'
                      f'      <grid name="glc">null</grid>\n'
                      f'      <grid name="wav">null</grid>\n'
                      f'      <mask>{ocn_grid}</mask>\n'
                      f'    </model_grid>\n')
        
        domain_name = (f'    <domain name="ne0np4_{dyn_grid}.pg2">\n'
                       f'      <nx>{self.get_ncol()}</nx>\n'
                       f'      <ny>1</ny>\n'
                       f'      <file grid="atm|lnd" mask="{ocn_grid}">{self.domain_files["lnd_domain_atm_ocn"]}</file>\n'
                       f'      <file grid="ice|ocn" mask="{ocn_grid}">{self.domain_files["ocn_domain_atm_ocn"]}</file>\n'
                       f'      <desc>{desc}</desc>\n'
                       f'    </domain>\n')
        
        gridmap_ocn = (f'    <gridmap atm_grid="ne0np4_{dyn_grid}.pg2" ocn_grid="{ocn_grid}">\n'
                       f'      <map name="ATM2OCN_FMAPNAME">{self.map_files["map_atm_to_ocn"]}</map>\n'
                       f'      <map name="ATM2OCN_SMAPNAME">{self.map_files["map_atm_to_ocn_bilin"]}</map>\n'
                       f'      <map name="ATM2OCN_VMAPNAME">{self.map_files["map_atm_to_ocn_bilin"]}</map>\n'
                       f'      <map name="OCN2ATM_FMAPNAME">{self.map_files["map_ocn_to_atm"]}</map>\n'
                       f'      <map name="OCN2ATM_SMAPNAME">{self.map_files["map_ocn_to_atm"]}</map>\n'
                       f'    </gridmap>\n')
        gridmap_lnd = (f'    <gridmap atm_grid="ne0np4_{dyn_grid}.pg2" lnd_grid="{lnd_grid}">\n'
                       f'      <map name="ATM2LND_FMAPNAME">{self.map_files["map_atm_to_lnd"]}</map>\n'
                       f'      <map name="ATM2LND_SMAPNAME">{self.map_files["map_atm_to_lnd_bilin"]}</map>\n'
                       f'      <map name="LND2ATM_FMAPNAME">{self.map_files["map_lnd_to_atm"]}</map>\n'
                       f'      <map name="LND2ATM_SMAPNAME">{self.map_files["map_lnd_to_atm"]}</map>\n'
                       f'    </gridmap>\n')
        gridmap_rof = (f'    <gridmap atm_grid="ne0np4_{dyn_grid}.pg2" rof_grid="{lnd_grid}">\n'
                       f'      <map name="ATM2ROF_FMAPNAME">{self.map_files["map_atm_to_lnd"]}</map>\n'
                       f'      <map name="ATM2ROF_SMAPNAME">{self.map_files["map_atm_to_lnd"]}</map>\n'
                       f'    </gridmap>\n')

        print(model_grid)
        print(domain_name)
        print(gridmap_ocn)
        print(gridmap_lnd)
        print(gridmap_ocn)
        
    def _horz_grid_txt(self, header=True, ncol='infer'):
        if header:
            self._print_filepath('components/eam/bld/config_files/horiz_grid.xml')
        if ncol == 'infer':
            ncol = self.get_ncol()            
        print(f'<horiz_grid dyn="se" hgrid="ne0np4_{self.variables["dyn_grid_name"]}.pg2"              ncol="{ncol}" csne="0" csnp="4" npg="2" />\n')
        
    def _namelist_defaults_eam_txt(self, header=True):
        if header:
            self._print_filepath('components/eam/bld/namelist_files/namelist_defaults_eam.xml')
        dyn_grid = self.variables['dyn_grid_name']
        out = (f'<dtime dyn="se"    hgrid="ne0np4_{dyn_grid}.pg2">900</dtime>\n'
               f'<ncdata dyn="se" hgrid="ne0np4_{dyn_grid}.pg2" nlev="72">{self.atm_ic["atm_ic"]}</ncdata>\n'
               f'<bnd_topo hgrid="ne0np4_{dyn_grid}" npg="2">{self.topography_file["topo"]}</bnd_topo>\n'
               f'<drydep_srf_file hgrid="ne0np4_{dyn_grid}" npg="2">{self.dry_deposition_file["atmsrf"]}</drydep_srf_file>\n'
               f'<se_ne hgrid="ne0np4_{dyn_grid}">0</se_ne>\n'
               f'<mesh_file hgrid="ne0np4_{dyn_grid}">{self.mesh_files["dyn_grid"]}</mesh_file>\n'
               f'<nu_top dyn_target="theta-l" hgrid="ne0np4_{dyn_grid}"> 1e5 </nu_top>\n'
               f'<se_tstep dyn_target="theta-l" hgrid="ne0np4_{dyn_grid}"> 75 </se_tstep>\n'
               f'<hypervis_subcycle dyn_target="theta-l" hgrid="ne0np4_{dyn_grid}"  > 2 </hypervis_subcycle>\n'
               f'<nu dyn_target="preqx" hgrid="ne0np4_{dyn_grid}">8.0e-8</nu>\n'
               f'<nu_div dyn_target="preqx" hgrid="ne0np4_{dyn_grid}">20.0e-8</nu_div>\n'
               f'<hypervis_scaling dyn_target="preqx" hgrid="ne0np4_{dyn_grid}">3.2</hypervis_scaling>\n'
               f'<se_nsplit dyn_target="preqx" hgrid="ne0np4_{dyn_grid}">4</se_nsplit>\n'
               f'<hypervis_subcycle hgrid="ne0np4_{dyn_grid}" dyn_target="preqx">7</hypervis_subcycle>\n'
               f'<fatmlndfrc hgrid="ne0np4_{dyn_grid}">{self.domain_files["lnd_domain_atm_ocn"]}</fatmlndfrc>\n'
               f'<focndomain hgrid="ne0np4_{dyn_grid}">{self.domain_files["ocn_domain_atm_ocn"]}</focndomain>')
        print(out)

if __name__ == "__main__":
    print('RRMHelper is a class to help in generating new RRM grids for the E3SM model')
    Helper = RRMHelper(script_dir='test', config_script='config.sh')
    Helper._locate_files()
    
