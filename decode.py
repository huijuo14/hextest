from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import base64
import json
import re
import html
from pydantic import BaseModel

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DecodeRequest(BaseModel):
    html_content: str = None
    single_entry: str = None

class ProxyDecoder:
    def decode_proxy_entry(self, encoded_str):
        try:
            padding = len(encoded_str) % 4
            if padding:
                encoded_str += '=' * (4 - padding)
            
            decoded_bytes = base64.b64decode(encoded_str)
            hex_string = decoded_bytes.decode('ascii')
            json_string = bytes.fromhex(hex_string).decode('ascii')
            
            return {
                "status": "success",
                "decoded_data": json.loads(json_string)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def extract_entries_from_html(self, html_content):
        try:
            unescaped_html = html.unescape(html_content)
            patterns = [r'data-ss="\[(.*?)\]"', r"data-ss='\[(.*?)\]'"]
            
            data_ss_content = None
            for pattern in patterns:
                match = re.search(pattern, unescaped_html, re.DOTALL)
                if match:
                    data_ss_content = match.group(1)
                    break
            
            if not data_ss_content:
                return []
            
            base64_pattern = r'["\']([A-Za-z0-9+/=]+)["\']'
            return re.findall(base64_pattern, data_ss_content)
        except Exception as e:
            return []
    
    def process_html(self, html_content):
        entries = self.extract_entries_from_html(html_content)
        if not entries:
            return {"status": "error", "message": "No entries found"}
        
        results = []
        success_count = 0
        
        for i, entry in enumerate(entries):
            result = self.decode_proxy_entry(entry)
            result["entry_number"] = i + 1
            result["preview"] = f"{entry[:20]}...{entry[-10:]}" if len(entry) > 40 else entry
            results.append(result)
            
            if result["status"] == "success":
                success_count += 1
        
        return {
            "status": "success",
            "statistics": {
                "total_entries": len(entries),
                "successful_decodes": success_count,
                "failed_decodes": len(entries) - success_count,
                "success_rate": f"{(success_count/len(entries))*100:.1f}%"
            },
            "results": results
        }

decoder = ProxyDecoder()

@app.post("/api/decode")
async def decode_data(request: DecodeRequest):
    try:
        if request.html_content:
            result = decoder.process_html(request.html_content)
            return JSONResponse(content=result)
        elif request.single_entry:
            result = decoder.decode_proxy_entry(request.single_entry)
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=400, detail="No input provided")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Proxy Decoder API is running"}

# Vercel requires this
@app.get("/api/decode")
async def decode_get():
    return {"message": "Use POST method to decode data"}
