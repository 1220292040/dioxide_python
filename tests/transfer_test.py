"""
转账功能测试用例
"""

import pytest
from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount


class TestTransfer:
    """转账功能测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.client = DioxClient()
        self.sender_pk = "pCrlpQ/VSj9pDbHGwdRJx9+Ck/26/LPnVbbUjDi7kfHqdcqDTB8Dd34vpQB4RUO4fP0eQIDAxTYwF/7a6gIr0w=="
        self.sender_account = DioxAccount.from_key(self.sender_pk)
        self.receiver_pk = "vJ2Pl7cXhr0TiIORl3Sfgfq+BPsIKEtIGF85mRd4fjHKZbnANBWRXPfHxvB44KuN3S/fqMLxjBxz6hA9vxKrMg=="
        self.receiver_account = DioxAccount.from_key(self.receiver_pk)

    def test_transfer_dio_token(self):
        """测试DIO代币转账"""
        # 执行转账
        tx_hash = self.client.transfer(
            self.sender_account,
            self.receiver_account.address,
            10,
            token="DIO",
            sync=True,
            timeout=60
        )

        # 验证交易哈希不为空
        assert tx_hash is not None, "转账应该返回交易哈希"
        assert isinstance(tx_hash, str), "交易哈希应该是字符串类型"
        assert len(tx_hash) > 0, "交易哈希不应该为空"

        # 验证账户对象已正确创建
        assert self.sender_account is not None, "发送方账户应该已创建"
        assert self.receiver_account is not None, "接收方账户应该已创建"
