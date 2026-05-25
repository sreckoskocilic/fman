from collections import namedtuple
from PyQt5.QtGui import QColor

import tinycss2

Rule = namedtuple('Rule', ('selectors', 'declarations'))
Declaration = namedtuple('Declaration', ('property', 'value'))

class CSSParseError(Exception):
	def __init__(self, message, line=0, column=0):
		super().__init__(message)
		self.line = line
		self.column = column
		self.reason = message

def parse_css(bytes_):
	result = []
	nodes = tinycss2.parse_stylesheet(
		bytes_.decode('utf-8'), skip_comments=True, skip_whitespace=True
	)
	for node in nodes:
		if node.type == 'error':
			raise CSSParseError(
				node.message, node.source_line, node.source_column
			)
		if node.type != 'qualified-rule':
			continue
		selector_str = tinycss2.serialize(node.prelude).strip()
		selectors = [s.strip() for s in selector_str.split(',')]
		declarations = []
		for decl in tinycss2.parse_declaration_list(
			node.content, skip_comments=True, skip_whitespace=True
		):
			if decl.type == 'error':
				raise CSSParseError(
					decl.message, decl.source_line, decl.source_column
				)
			if decl.type == 'declaration':
				value = tinycss2.serialize(decl.value).strip()
				declarations.append(Declaration(decl.name, value))
		result.append(Rule(selectors, declarations))
	return result

class CSSEngine:
	def __init__(self, parsed_css):
		self._rules = parsed_css
	def parse_border_width(self, selector, declaration):
		value = self._query(selector, declaration)
		width = value.split(' ')[0]
		error_message = \
			'Invalid value for %s %s: %r. Should be of the form ' \
			'"123px solid #ff0000".' % (selector, declaration, value)
		if not width.endswith('px'):
			raise ValueError(error_message)
		try:
			return int(width[:-2])
		except ValueError:
			raise ValueError(error_message) from None
	def parse_pts(self, selector, declaration):
		value = self._query(selector, declaration)
		error_message = \
			'Invalid pt value for %s %s: %r' % (selector, declaration, value)
		if not value.endswith('pt'):
			raise ValueError(error_message)
		try:
			return int(value[:-2])
		except ValueError:
			raise ValueError(error_message) from None
	def parse_color(self, selector, declaration):
		value = self._query(selector, declaration)
		return QColor(value)
	def parse_px(self, selector, declaration):
		value = self._query(selector, declaration)
		error_message = \
			'Invalid px value for %s %s: %r' % (selector, declaration, value)
		if not value.endswith('px'):
			raise ValueError(error_message)
		try:
			return int(value[:-2])
		except ValueError:
			raise ValueError(error_message) from None
	def _query(self, selector, declaration):
		declarations = self._get_declarations(selector)
		try:
			return declarations[declaration]
		except KeyError:
			raise ValueError(
				'Could not find %s for %s' % (declaration, selector)
			)
	def _get_declarations(self, selector):
		result = {}
		for rule in self._rules:
			for sel in rule.selectors:
				if sel == '*' or sel == selector:
					for declaration in rule.declarations:
						result[declaration.property] = declaration.value
		return result
