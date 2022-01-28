from glob import glob
import os
import subprocess
import warnings
import re

class BashParser:
    """ Parse a bash script to extract variables
    """
    
    def __init__(self, script):
        self.script = script
        self._lines = []
        self.variables = dict()
        
    def _readlines(self):
        if not os.path.isfile(self.script):
            warnings.warn(f'{self.script} does not exist')
            return
        with open(self.script) as FILE:
            self._lines = FILE.readlines()
    
    def _strip_lines(self):
        """Drop comment lines, blank lines, and whitespace from self._lines"""
        if not self._lines:
            self._readlines()
        self._lines = [line.strip() for line in self._lines 
                       if line[0] != "#" and line != '\n']
    
    def _expand_var(self, var, do_eval=True):
        """ expand ${var}, $var, or `var` into what it should be """

        # patterns to match ${var} or $var
        pattern = '(\$\{[a-zA-Z0-9_]*\}|\$[a-zA-Z0-9_]*)'
        
        var = var.split('#')[0].strip()
        keys = re.findall(pattern, var)
        for key in keys:
            stripped_key = key
            for char in '${}':
                stripped_key = stripped_key.replace(char, '')
            if stripped_key in self.variables.keys():
                var = var.replace(key, self.variables[stripped_key])
            elif stripped_key == 'PWD':
                # special case: PWD refers to script directory
                var = var.replace(key, os.path.split(self.script)[0])
            elif stripped_key in os.environ:
                var = var.replace(key, os.environ[stripped_key])
        
        if do_eval and '`' in var:
            exprs = re.findall('`([^`]*)`', var)
            # evaluate each expression and replace
            for expr in exprs:
                args = expr.split()
                output = subprocess.run(args, capture_output=True).stdout.decode().strip()
                var = var.replace(f'`{expr}`', output)
        return var
    
    def _expand_conditional(self, line):
        """ expand 'if [ cond ]; then' and evaluate cond"""
        pattern = '(\$\{[a-zA-Z0-9_]*\}|\$[a-zA-Z0-9_]*)'
        keys = re.findall(pattern, line)
        for key in keys:
            stripped_key = key
            for char in '${}':
                stripped_key = stripped_key.replace(char, '')
            if stripped_key in self.variables.keys():
                line = line.replace(key, self.variables[stripped_key])
            elif stripped_key in os.environ:
                line = line.replace(key, os.environ[stripped_key])

        # drop everything except the conditional to be evaluated:
        # all have form '"a" == "b"' ...
        line_as_list = line.split()
        eq_pos = line_as_list.index('==')
        cond = line_as_list[eq_pos - 1] == line_as_list[eq_pos + 1]
        return line, cond
    
    def parse(self, verbose=False):
        if not self._lines:
            self._strip_lines()

        do_parse = True
        for i, line in enumerate(self._lines):
            # check for conditional
            if line.lstrip()[0:2] == 'if':
                # conditional line starts now -- if it evals to true, then continue parse. 
                # Else, skip to the next conditional
                new_line, do_parse = self._expand_conditional(line)
                if verbose:
                    if do_parse:
                        print('we have a match!', new_line)
                    else:
                        print('skipping ...', new_line)
            elif line.lstrip() == 'fi':
                # exiting conditional - return to parsing
                do_parse = True
                if verbose:
                    print(i, 'out of if block')
            if not do_parse:
                continue
            # commence parsing
            if '=' in line and '==' not in line:
                k, v = line.strip().split('=')
                self.variables[k] = self._expand_var(v)
        return self.variables


if __name__ == "__main__":
    test_script = 'test/config.sh'
    print('contents of test script: ')
    print('------ config.sh ---------------')
    with open(test_script, 'r') as FILE:
        raw_contents = FILE.readlines()
    print(*raw_contents)
    print('--------------------------------\n\n')
    
    print('Parsed contents: ')
    Test = BashParser('test/config.sh')
    print(Test.parse())
