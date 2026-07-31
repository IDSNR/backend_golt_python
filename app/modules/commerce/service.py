class CommerceService:
    def __init__(self) -> None:
        self.purchases: list[dict] = []

    def create_purchase(self, profile_id: str, payload: dict) -> dict:
        purchase = {
            'id': f'purchase-{len(self.purchases) + 1}',
            'profileId': profile_id,
            'contentId': payload.get('contentId'),
            'amountCents': payload.get('amountCents', 0),
            'status': 'completed',
        }
        self.purchases.append(purchase)
        return purchase

    def get_content_attribution(self, content_id: str) -> dict:
        content_purchases = [p for p in self.purchases if p.get('contentId') == content_id]
        return {
            'purchaseCount': len(content_purchases),
            'totalRevenueCents': sum(p.get('amountCents', 0) for p in content_purchases),
        }
