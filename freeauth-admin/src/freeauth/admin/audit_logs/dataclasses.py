# Copyright (c) 2016-present DecentFoX Studio and the FreeAuth authors.
# FreeAuth is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan
# PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import enum

from freeauth.db.auth.auth_qry_async_edgeql import (
    FreeauthAuditStatusCode as SC,
)


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
    SC.INVALID_CODE: "验证码错误或已失效，请重新获取",
    SC.CODE_INCORRECT: "验证码错误，请重新输入",
    SC.CODE_ATTEMPTS_EXCEEDED: (
        "您输入的错误验证码次数过多，当前验证码已失效，请重新获取"
    ),
    SC.CODE_EXPIRED: "验证码已失效，请重新获取",
}
