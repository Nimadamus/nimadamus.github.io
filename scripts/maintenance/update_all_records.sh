#!/bin/bash

# NFL
sed -i 's|https://docs.google.com/spreadsheets/d/e/2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv/pub?output=csv|https://docs.google.com/spreadsheets/d/e/2PACX-1vQgB4WcyyEpMBp_XI_ya6hC7Y8kRaHzrOvuLMq9voGF0nzfqi4lkmAWVb92nDkxUhLVhzr4RTWtZRxq/pub?output=csv|g' nfl-records.html

# NHL
sed -i 's|https://docs.google.com/spreadsheets/d/e/2PACX-1vQjW2l6hBUafumAiOdJblACLIx3GTtdJDcytUcN1nu2QHJmHnUMN9_5Tp2v7VqMTZaATfdmcJ-SK4jD/pub?output=csv|https://docs.google.com/spreadsheets/d/e/2PACX-1vRaRwsGOmbXrqAX0xqrDc9XwRCSaAOkuW68TArz3XQp7SMmLirKbdYqU5-zSM_A-MDNKG6sbdwZac6I/pub?output=csv|g' nhl-records.html

# NBA
sed -i 's|https://docs.google.com/spreadsheets/d/e/2PACX-1vQjW2l6hBUafumAiOdJblACLIx3GTtdJDcytUcN1nu2QHJmHnUMN9_5Tp2v7VqMTZaATfdmcJ-SK4jD/pub?output=csv|https://docs.google.com/spreadsheets/d/e/2PACX-1vSBoPl-dhj7ZAVpRIafqrFBf10r6sg3jpEKxmuymugAckdoMp-czkj1hscpDnV42GGJsIvNx5EniLVz/pub?output=csv|g' nba-records.html

# MLB
sed -i 's|https://docs.google.com/spreadsheets/d/e/2PACX-1vQjW2l6hBUafumAiOdJblACLIx3GTtdJDcytUcN1nu2QHJmHnUMN9_5Tp2v7VqMTZaATfdmcJ-SK4jD/pub?output=csv|https://docs.google.com/spreadsheets/d/e/2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv/pub?output=csv|g' betlegend-verified-records.html

# Soccer
sed -i 's|https://docs.google.com/spreadsheets/d/e/2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv/pub?output=csv|https://docs.google.com/spreadsheets/d/e/2PACX-1vQy0EQskvixsVQb1zzYtCKDa4F1Wl6WU5QuAFMit32vms-c4DxlhLik-k7U_EhuYntQrpw4BI6r0rns/pub?output=csv|g' soccer-records.html

echo "✅ Updated NFL records page"
echo "✅ Updated NHL records page"
echo "✅ Updated NBA records page"
echo "✅ Updated MLB records page"
echo "✅ Updated Soccer records page"
echo "✅ NCAAF already correct"
echo "✅ NCAAB using master sheet (empty)"
