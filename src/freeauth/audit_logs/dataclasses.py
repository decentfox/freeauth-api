import enum

from ..query_api import AuthAuditStatusCode as SC


class AuthAuditEventType(enum.Enum):
    SIGNIN = "SignIn"
    SIGNOUT = "SignOut"
    SIGNUP = "SignUp"


AUDIT_STATUS_CODE_MAPPING = {
    SC.OK: "成功",
    SC.ACCOUNT_NOT_EXISTS: "账号不存在，请您确认登录信息输入是否正确",
    SC.ACCOUNT_DISABLED: "您的账号已停用",
    SC.PASSWORD_ATTEMPTS_EXCEEDED: "密码连续多次输入错误，账号暂时被锁定",
    SC.INVALID_PASSWORD: "密码输入错误",
}
