# Troubleshooting Guide

## n8n Issues

### "? mark" on nodes (nodes not recognized)
**Cause:** n8n 2.x removed the `executeCommand` node.
**Fix:** This repo uses Code nodes with `child_process.execSync` instead. Ensure env vars are set:
```yaml
NODE_FUNCTION_ALLOW_BUILTIN=*
NODE_FUNCTION_ALLOW_EXTERNAL=*
```

### "Access to the file is not allowed"
**Cause:** `readWriteFile` node is restricted to `/root/.n8n-files` in n8n 2.x.
**Fix:** Already resolved — workflow uses `fs.readFileSync` in Code node instead.

### n8n won't start / keeps restarting
**Cause:** Usually a bad `N8N_ENCRYPTION_KEY` or missing env vars.
**Fix:** Check logs: `docker logs n8n-setup-n8n-1 --tail 30`

## Unstract Issues

### Upload to Unstract returns 400/401
- Check API key is correct in the n8n credential
- Check the URL org slug matches your Unstract deployment
- Verify Unstract containers are all running: `docker ps | grep unstract`

### Workflow completes but invoice_data is empty
**Cause:** Unstract API is async — the poll loop didn't find the result.
**Debug:** Open "Poll & Parse Unstract Result" node output in n8n. Check:
- `parseOk` field — if false, result was empty
- The poll loop tries every 10s for 10 minutes
- Check Unstract logs: `docker logs unstract-backend --tail 50`

### Unstract returns PENDING forever
- The LLM model may be overloaded
- Check Unstract worker: `docker logs unstract-worker --tail 30`
- Restart workers: `docker restart unstract-worker unstract-worker-file-processing`

## Excel Issues

### "No such file" on LB.xlsx
The file must exist before the workflow runs. Create it manually or copy the template.
The automation does NOT create LB.xlsx from scratch.

### Excel write fails / file locked
- Close LB.xlsx in Excel before running the workflow
- The Python script has retry logic (5 attempts, 2s delay)

## Docker Issues

### "unstract-network not found"
```powershell
docker network ls
# Find your actual Unstract network name, then update docker-compose.yml
```

### Python not found in container
The Dockerfile copies Python from `python:3.12-alpine`. If build fails:
```powershell
docker pull python:3.12-alpine
cd C:\Users\YOUR_USERNAME\Desktop\n8n-setup
docker-compose build --no-cache
```

## File Not Being Processed

1. Check the file is in the root of the invoices folder (not a subfolder)
2. Check the file extension is `.pdf`, `.PDF`, `.jpg`, `.JPG`, `.jpeg`, or `.JPEG`
3. Check n8n workflow is Active (toggle in UI)
4. Check volume mount: `docker inspect n8n-setup-n8n-1 | grep Binds`
