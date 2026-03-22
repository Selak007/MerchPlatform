import os
import json
import re
import pg8000.native

# Database credentials (in practice, use AWS Secrets Manager or secure ENV params)
DB_HOST = os.environ.get('DB_HOST', 'db-visa-1.ct8s8cg26mzr.us-east-2.rds.amazonaws.com')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'visabank123')
DB_PORT = int(os.environ.get('DB_PORT', 5432))

def get_db_connection():
    """Establish and return a pg8000.native database connection."""
    return pg8000.native.Connection(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )


# --- AGENT OPERATION HANDLERS ---

def get_merchant_performance(merchant_id):
    """
    Bedrock Agent operation to fetch merchant performance, ticket size, and health statistics.
    """
    con = None
    try:
        con = get_db_connection()
        # Query overview from merchants table
        merchant_query = "SELECT merchant_name, merchant_category, avg_ticket_size, risk_level FROM merchants WHERE merchant_id = :id"
        merchant_data = con.run(merchant_query, id=merchant_id)

        if not merchant_data:
            return {"status": "error", "message": f"Merchant ID {merchant_id} not found."}

        # Query total auth stats
        auth_stats_query = """
            SELECT 
                COUNT(*) as total_txns, 
                SUM(amount) as total_volume,
                SUM(CASE WHEN auth_status = 'APPROVED' THEN 1 ELSE 0 END) as approved_count 
            FROM authorization_transactions 
            WHERE merchant_id = :id
        """
        auth_stats = con.run(auth_stats_query, id=merchant_id)

        # Build response
        merchant_info = merchant_data[0]
        stats = auth_stats[0]
        approval_rate = (stats[2] / stats[0] * 100) if stats[0] > 0 else 0

        return {
            "merchant_name": merchant_info[0],
            "category": merchant_info[1],
            "avg_ticket_size": float(merchant_info[2]) if merchant_info[2] else 0.0,
            "risk_level": merchant_info[3],
            "transaction_count": stats[0],
            "total_volume": float(stats[1]) if stats[1] else 0.0,
            "approval_rate": round(approval_rate, 2)
        }

    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}
    finally:
        if con:
            con.close()


def get_settlement_status(auth_id):
    """
    Bedrock Agent operation to check settlement status for a given transaction.
    """
    con = None
    try:
        con = get_db_connection()
        query = """
            SELECT 
                s.settlement_amount, 
                s.settlement_currency, 
                s.settlement_date, 
                s.settlement_status,
                s.network_fee,
                a.merchant_id
            FROM settlement_transactions s
            JOIN authorization_transactions a ON s.auth_id = a.auth_id
            WHERE s.auth_id = :auth_id
        """
        result = con.run(query, auth_id=auth_id)

        if not result:
            return {"status": "error", "message": f"No settlement found for auth_id: {auth_id}"}
        
        row = result[0]
        return {
            "status": "success",
            "auth_id": auth_id,
            "merchant_id": row[5],
            "settlement_amount": float(row[0]) if row[0] else 0.0,
            "currency": row[1],
            "date": str(row[2]) if row[2] else None,
            "settlement_status": row[3],
            "network_fee": float(row[4]) if row[4] else 0.0
        }

    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}
    finally:
        if con:
            con.close()


def get_fraud_alerts(merchant_id):
    """
    Bedrock Agent operation to fetch active fraud alerts for a given merchant.
    """
    con = None
    try:
        con = get_db_connection()
        query = """
            SELECT f.fraud_type, f.risk_score, f.fraud_reason, f.detected_time
            FROM fraud_events f
            JOIN authorization_transactions a ON f.auth_id = a.auth_id
            WHERE a.merchant_id = :id AND f.risk_score > 70
            ORDER BY f.detected_time DESC
            LIMIT 5
        """
        results = con.run(query, id=merchant_id)
        
        alerts = []
        for row in results:
            alerts.append({
                "fraud_type": row[0],
                "risk_score": row[1],
                "reason": row[2],
                "detected_time": str(row[3])
            })
            
        return {
            "merchant_id": merchant_id,
            "critical_fraud_alerts_count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if con:
            con.close()


# --- LAMBDA HANDLER ---

def lambda_handler(event, context):
    """
    AWS Bedrock Agent Action Group Lambda Handler
    """
    print(f"Received Event: {json.dumps(event)}")
    
    agent = event.get('agent', '')
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    # Extract parameters
    param_dict = {p.get('name'): p.get('value') for p in parameters}
    
    response_body = {}
    
    try:
        # Route to the appropriate function based on the API schema definition
        if function == 'get_merchant_performance':
            merchant_id = int(param_dict.get('merchant_id', 0))
            response_body = get_merchant_performance(merchant_id)
            
        elif function == 'get_settlement_status':
            auth_id = param_dict.get('auth_id', '')
            response_body = get_settlement_status(auth_id)
            
        elif function == 'get_fraud_alerts':
            merchant_id = int(param_dict.get('merchant_id', 0))
            response_body = get_fraud_alerts(merchant_id)
            
        else:
            response_body = {"status": "error", "message": f"Function {function} not supported"}

    except Exception as e:
        response_body = {"status": "error", "message": str(e)}
        
    # Standard Bedrock Agent Response Format
    response = {
        "response": {
            "actionGroup": action_group,
            "function": function,
            "functionResponse": {
                "responseBody": {
                    "application/json": {
                        "body": json.dumps(response_body)
                    }
                }
            }
        }
    }
    
    print(f"Response: {json.dumps(response)}")
    return response
