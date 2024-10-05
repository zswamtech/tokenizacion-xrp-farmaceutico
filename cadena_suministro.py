import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import TrustSet, Payment
from xrpl.transaction import submit_and_wait, sign
from xrpl.models.requests import Ledger, AccountInfo, Fee

# Connect to the XRP Ledger Testnet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")

# Create wallets for the supplier (emitter) and hospital (receiver)
emisor_wallet = Wallet.from_seed("sEdT1QNqH9PqDCyfriZnWJ9vFbTDsLs")
receptor_wallet = Wallet.from_seed("sEd7Y1i55pZJDNzDhCivG8yw4M6RNv8")

# Verify the addresses of the accounts
print(f"Proveedor (emisor): {emisor_wallet.classic_address}")
print(f"Hospital (receptor): {receptor_wallet.classic_address}")

# Fetch the current ledger index to set the last_ledger_sequence
ledger_info = client.request(Ledger()).result
print(f"Ledger info response: {ledger_info}")

# Access the ledger_index from the closed ledger section
current_ledger_index = ledger_info["closed"]["ledger"]["ledger_index"]
last_ledger_sequence = current_ledger_index + 10  # Set the expiration after 4 ledgers

# Fetch the current sequence number for the receiver's account
account_info_response = client.request(AccountInfo(account=receptor_wallet.classic_address)).result
receptor_account_sequence = account_info_response["account_data"]["Sequence"]
print(f"Hospital account sequence: {receptor_account_sequence}")

# Fetch the current transaction fee
fee_response = client.request(Fee()).result
current_fee = fee_response["drops"]["base_fee"]
print(f"Current fee (in drops): {current_fee}")

# Step 1: Create a trustline between the supplier and the hospital
trust_set_txn = TrustSet(
    account=receptor_wallet.classic_address,
    limit_amount={
        "currency": "MED",  # Token representing the medicine (3-character code)
        "issuer": emisor_wallet.classic_address,  # Supplier's (emitter) address
        "value": "1000"  # Trustline limit (maximum number of tokens the receiver accepts)
    },
    last_ledger_sequence=last_ledger_sequence,  # Add the last_ledger_sequence
    sequence=receptor_account_sequence,  # Add the current sequence number for the receiver
    fee=current_fee  # Add the current fee
)

# Sign and submit the TrustSet transaction
signed_trust_set_txn = sign(trust_set_txn, receptor_wallet)
trust_set_response = submit_and_wait(signed_trust_set_txn, client)
print(f"TrustSet completed: {trust_set_response}")

# Step 2: Fetch the current sequence number for the supplier's account
account_info_response = client.request(AccountInfo(account=emisor_wallet.classic_address)).result
emisor_account_sequence = account_info_response["account_data"]["Sequence"]
print(f"Proveedor account sequence: {emisor_account_sequence}")

# Token issuance from the supplier to the hospital
token_payment_txn = Payment(
    account=emisor_wallet.classic_address,
    amount={
        "currency": "MED",  # Token for the medicine
        "value": "500",  # Amount of tokens to issue (500 units of medicine)
        "issuer": emisor_wallet.classic_address
    },
    destination=receptor_wallet.classic_address,
    last_ledger_sequence=last_ledger_sequence,  # Add the last_ledger_sequence
    sequence=emisor_account_sequence,  # Add the current sequence number for the supplier
    fee=current_fee  # Add the current fee
)

# Sign and submit the token issuance transaction
signed_token_payment_txn = sign(token_payment_txn, emisor_wallet)
token_payment_response = submit_and_wait(signed_token_payment_txn, client)
print(f"Medicine tokens issued: {token_payment_response}")
