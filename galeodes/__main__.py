from warnings import filterwarnings
filterwarnings('ignore', category=RuntimeWarning, module='runpy')

def main_logic():
	from galeodes import Galeodes
	from argparse import ArgumentParser, SUPPRESS

	class _ArgumentParser(ArgumentParser):
		def error(self, message):
			self.exit(2, 'Error: %s\n' % (message))

	ARG_PARSER = _ArgumentParser(description='Qeeqbox/galeodes', usage=SUPPRESS)
	ARG_PARSER._action_groups.pop()
	ARG_PARSER_DRIVERS = ARG_PARSER.add_argument_group('Drivers')
	ARG_PARSER_DRIVERS.add_argument('--driver', help='Get latest chrome or firefox driver', metavar='', default='')
	ARGV = ARG_PARSER.parse_args()
	if ARGV.driver:
		if ARGV.driver == "chrome" or ARGV.driver == "firefox":
			print(Galeodes(browser=ARGV.driver).get_driver())

if __name__ == '__main__':
    main_logic()