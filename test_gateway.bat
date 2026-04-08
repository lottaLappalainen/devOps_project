@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo        FULL SYSTEM VERIFICATION SCRIPT - COMP.SE.140
echo ============================================================
echo Tests: AUTH, SWITCH, DISCARD, LOG, MONITORING, HTTPS, API
echo ============================================================
echo.

:: ================= CONFIG =================
set GATEWAY=http://localhost:8198
set API=http://localhost:8199
set AUTH=admin:1234

echo Using GATEWAY: %GATEWAY%
echo Using API: %API%
echo Using USER: %AUTH%
echo.

:: ============================================================
echo ================== AUTHENTICATION =========================
:: ============================================================

echo.
echo ---- TEST 1: ACCESS GATEWAY WITHOUT LOGIN (MUST BE 401) ----
curl -I %GATEWAY%
echo EXPECTED: 401 Unauthorized
pause

echo.
echo ---- TEST 2: LOGIN WITH CORRECT CREDENTIALS ----
curl -I --user %AUTH% %GATEWAY%
echo EXPECTED: 200 OK
pause

echo.
echo ---- TEST 3: LOGIN WITH WRONG PASSWORD ----
curl -I --user admin:wrong %GATEWAY%
echo EXPECTED: 401 Unauthorized
pause


:: ============================================================
echo ================== GATEWAY OPS ============================
:: ============================================================

echo.
echo ---- TEST 4: GATEWAY ROOT WITH AUTH ----
curl --user %AUTH% %GATEWAY%
echo EXPECTED: gateway OK response
pause


:: ============================================================
echo ================== BLUE-GREEN SWITCH ======================
:: ============================================================

echo.
echo ---- TEST 5: SWITCH VERSION (BLUE <-> GREEN) ----
curl -X POST --user %AUTH% %GATEWAY%/switch
echo EXPECTED: "switched" or similar confirmation
pause

timeout /t 2 >nul

echo.
echo ---- TEST 6: VERIFY SWITCH BY CHECKING DIRECT API STATUS ----
curl %API%/status
echo EXPECTED: version CHANGED from previous
pause

echo.
echo ---- TEST 7: DISCARD OLD VERSION ----
curl -X POST --user %AUTH% %GATEWAY%/discard
echo EXPECTED: discard completed
pause

timeout /t 2 >nul

echo.
echo ---- TEST 8: VERIFY DISCARD BY STATUS ----
curl %API%/status
echo EXPECTED: API VERSION == v1 after discard
pause


:: ============================================================
echo ================== DIRECT API TESTS =======================
:: ============================================================

echo.
echo ---- TEST 9: DIRECT API STATUS ----
curl %API%/status
echo EXPECTED: uptime, free disk, version, service2 line
pause

echo.
echo ---- TEST 10: DIRECT API LOG ----
curl %API%/log
echo EXPECTED: log entries printed
pause

echo.
echo ---- TEST 11: DIRECT API RESET ----
curl -X POST %API%/reset
echo EXPECTED: ok
pause

echo.
echo ---- TEST 12: VERIFY LOG IS EMPTY ----
curl %API%/log
echo EXPECTED: empty log
pause


:: ============================================================
echo ================== SERVICE2 CHECK =========================
:: ============================================================

echo.
echo ---- TEST 13: SERVICE2 STATUS (called internally by API) ----
curl %API%/status
echo EXPECTED: second line includes service2 response
pause


:: ============================================================
echo ================== MONITORING =============================
:: ============================================================

echo.
echo ---- TEST 14: MONITORING/METRICS ----
curl --user %AUTH% %GATEWAY%/monitoring/metrics
echo EXPECTED:
echo   - container uptimes
echo   - CPU usage
echo   - Memory usage
echo   - Log size
pause

echo.
echo ---- TEST 15: CONTAINER STATUS ----
docker ps
echo EXPECTED:
echo   gateway
echo   api_v1
echo   api_v2
echo   service2
echo   storage
echo   monitoring
pause


:: ============================================================
echo ================== HTTPS TESTING ==========================
:: ============================================================

echo.
echo ---- TEST 16: HTTPS GATEWAY ROOT ----
curl -I -k https://localhost:8198/
echo EXPECTED: 401 (not logged in) or 200 (if cert accepted)
pause

echo.
echo ---- TEST 17: HTTPS STATUS THROUGH GATEWAY AUTH ----
curl -k --user %AUTH% https://localhost:8198/
echo EXPECTED: gateway OK
pause


:: ============================================================
echo ================== VERSION FORMAT =========================
:: ============================================================

echo.
echo ---- TEST 18: VERSION FORMAT / UPTIME UNIT ----
curl %API%/status
echo EXPECTED:
echo   - project1.0  -> uptime in HOURS
echo   - project1.1  -> uptime in MINUTES
pause


:: ============================================================
echo ================== EXTRA SAFETY TESTS =====================
:: ============================================================

echo.
echo ---- TEST 19: STORAGE CONTAINER DIRECT LOG ----
curl http://localhost:8200/log
echo EXPECTED: log content (same as API/log)
pause

echo.
echo ---- TEST 20: STORAGE RESET ----
curl -X POST http://localhost:8200/reset
echo EXPECTED: ok
pause

echo.
echo ---- TEST 21: HEALTH OF ALL CONTAINERS ----
docker inspect -f "{{.State.Health.Status}}" gateway 2>nul
docker inspect -f "{{.State.Health.Status}}" api_v1 2>nul
docker inspect -f "{{.State.Health.Status}}" api_v2 2>nul
docker inspect -f "{{.State.Health.Status}}" storage 2>nul
docker inspect -f "{{.State.Health.Status}}" service2 2>nul
echo EXPECTED: all healthy
pause


echo.
echo ============================================================
echo              ALL AUTOMATED TESTS FINISHED
echo ============================================================
echo  If ALL EXPECTED RESULTS MATCH -> SYSTEM FULLY WORKING
echo ============================================================
pause
