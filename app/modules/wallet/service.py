class WalletService:
    def __init__(self) -> None:
        self.balances: dict[str, int] = {}

    def _get_balance(self, user_id: str) -> int:
        return self.balances.get(user_id, 0)

    def get_balance(self, user_id: str) -> int:
        return self._get_balance(user_id)

    def withdraw(self, user_id: str, amount_cents: int) -> int:
        if amount_cents < 0:
            raise ValueError('amountCents must be a non-negative integer')
        current = self._get_balance(user_id)
        self.balances[user_id] = max(0, current - amount_cents)
        return self.balances[user_id]

    def boost_purchase(self, user_id: str, cost_cents: int) -> dict:
        if cost_cents < 0:
            raise ValueError('costCents must be a non-negative integer')
        current = self._get_balance(user_id)
        if current >= cost_cents:
            self.balances[user_id] = current - cost_cents
            return {
                'walletDebitCents': cost_cents,
                'cardChargeCents': 0,
                'newBalance': self.balances[user_id],
            }
        raise ValueError('No card on file or insufficient wallet balance')
