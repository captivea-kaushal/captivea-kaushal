-- disable stancer payment provider
UPDATE payment_provider
   SET stancer_key_client = NULL,
       stancer_key_secret = NULL,
