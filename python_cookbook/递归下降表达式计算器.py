import re
import collections

# 定义词法单元的正则表达式模式
NUM = r'(?P<NUM>\d+)'          # 匹配数字
PLUS = r'(?P<PLUS>\+)'         # 匹配加号
MINUS = r'(?P<MINUS>-)'        # 匹配减号
TIMES = r'(?P<TIMES>\*)'       # 匹配乘号
DIVIDE = r'(?P<DIVIDE>/)'      # 匹配除号
LPAREN = r'(?P<LPAREN>\()'     # 匹配左括号
RPAREN = r'(?P<RPAREN>\))'     # 匹配右括号
WS = r'(?P<WS>\s+)'            # 匹配空白字符

# 编译所有模式为一个正则表达式，用于词法分析
masterPat = re.compile('|'.join([NUM, PLUS, MINUS, TIMES, DIVIDE, LPAREN, RPAREN, WS]))

# 定义 Token 类型，使用 namedtuple 存储类型和值
Token = collections.namedtuple('Token', ['type', 'value'])

def generateTokens(text):
    """词法分析器：将输入文本分解为 Token 序列，忽略空白字符"""
    scanner = masterPat.scanner(text)  # 创建扫描器
    for m in iter(scanner.match, None):  # 迭代匹配，直到结束
        tok = Token(m.lastgroup, m.group())  # 创建 Token
        if tok.type != 'WS':  # 忽略空白字符
            yield tok

# 表达式解析器类
class ExpressionEvaluator:
    """
    递归下降解析器的实现。每个方法对应一个语法规则。
    使用 _accept() 测试并接受当前前瞻 Token,使用 _expect() 严格匹配并消费 Token。
    """

    def parse(self, text):
        """解析入口：初始化 Token 流并调用 expr() 开始解析"""
        self.tokens = generateTokens(text)  # 生成 Token 迭代器
        self.tok = None  # 当前 Token
        self.nexttok = None  # 下一个 Token（前瞻）
        self._advance()  # 前进到第一个 Token
        return self.expr()  # 开始解析表达式
    
    def _advance(self):
        """前进一步，将下一个 Token 移到当前，并获取新的下一个 Token"""
        self.tok, self.nexttok = self.nexttok, next(self.tokens, None)
    
    def _accept(self, toktype):
        """测试并接受下一个 Token,如果类型匹配则前进"""
        if self.nexttok and self.nexttok.type == toktype:
            self._advance()
            return True
        return False

    def _expect(self, toktype):
        """严格匹配并消费下一个 Token,若不匹配则抛出语法错误"""
        if not self._accept(toktype):
            raise SyntaxError(f'期望 {toktype}，但未找到')

    # 语法规则实现
    def expr(self):
        """表达式规则: expr ::= term { ('+'|'-') term }*"""
        exprval = self.term()  # 解析第一个 term
        # 处理连续的加减法
        while self._accept('PLUS') or self._accept('MINUS'):
            op = self.tok.type  # 获取运算符类型
            right = self.term()  # 解析右侧 term
            if op == 'PLUS':
                exprval = ('+', exprval, right)  # 生成加法元组
            elif op == 'MINUS':
                exprval = ('-', exprval, right)  # 生成减法元组
        return exprval
    
    def term(self):
        """项规则: term ::= factor { ('*'|'/') factor }*"""
        termval = self.factor()  # 解析第一个 factor
        # 处理连续的乘除法
        while self._accept('TIMES') or self._accept('DIVIDE'):
            op = self.tok.type  # 获取运算符类型
            right = self.factor()  # 解析右侧 factor
            if op == 'TIMES':
                termval = ('*', termval, right)  # 生成乘法元组
            elif op == 'DIVIDE':
                termval = ('/', termval, right)  # 生成除法元组
        return termval
    
    def factor(self):
        """因子规则: factor ::= NUM | ( expr )"""
        if self._accept('NUM'):
            return int(self.tok.value)  # 返回数字值
        elif self._accept('LPAREN'):
            exprval = self.expr()  # 解析括号内的表达式
            self._expect('RPAREN')  # 必须有右括号
            return exprval
        else:
            raise SyntaxError('期望数字或左括号')

def descentParser():
    """测试函数"""
    e = ExpressionEvaluator()
    print(e.parse('2'))
    print(e.parse('2 + 3'))
    print(e.parse('2 + 3 * 4'))
    print(e.parse('2 + (3 + 4) * 5'))

if __name__ == '__main__':
    descentParser()