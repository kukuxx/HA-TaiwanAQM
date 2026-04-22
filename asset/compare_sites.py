"""
比對環保署空氣品質監測站點資料
"""
import csv
import json
import sys
import os
import subprocess
import unicodedata
import re

from typing import List, Dict, Set, Tuple
from datetime import datetime

import requests

class SiteComparator:
    def __init__(self, api_url: str, expected_file: str):
        self.api_url = api_url
        self.expected_file = expected_file
        self.api_sites: Set[Tuple[str, str, str]] = set()
        self.expected_sites: Set[Tuple[str, str, str]] = set()

    def _fetch_api_data(self) -> None:
        """從 API 下載 CSV 資料並解析（最多重試5次）"""
        print("📡 正在下載 API 資料...")

        max_retries = 5

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(self.api_url, timeout=30, verify=False)
                response.raise_for_status()

                content = response.content.decode('utf-8-sig')
                csv_reader = csv.DictReader(content.splitlines())

                for row in csv_reader:
                    siteid = self._clean(row.get('siteid', ''))
                    sitename = self._clean(row.get('sitename', ''))
                    county = self._clean(row.get('county', ''))

                    if siteid and sitename and county:
                        self.api_sites.add((siteid, sitename, county))

                if self.api_sites:
                    print(f"✅ 成功取得 {len(self.api_sites)} 個站點 (嘗試第 {attempt} 次)")
                    return
                else:
                    print(f"⚠️ 第 {attempt} 次取得 0 筆資料，重試中...")

            except requests.exceptions.RequestException as e:
                print(f"❌ 第 {attempt} 次下載失敗: {e}", file=sys.stderr)

            except Exception as e:
                print(f"❌ 第 {attempt} 次資料處理失敗: {e}", file=sys.stderr)

        # 全部重試失敗
        print("❌ 重試 5 次仍然無法取得有效資料", file=sys.stderr)
        sys.exit(1)

    def _load_expected_data(self) -> None:
        """載入預期的站點資料"""
        print("📂 正在載入預期站點資料...")
        try:
            with open(self.expected_file, 'r', encoding='utf-8-sig') as f:
                csv_reader = csv.DictReader(f)
                
                for row in csv_reader:
                    siteid = self._clean(row.get('siteid', ''))
                    sitename = self._clean(row.get('sitename', ''))
                    county = self._clean(row.get('county', ''))
                    
                    if siteid and sitename and county:
                        self.expected_sites.add((siteid, sitename, county))
            
            print(f"✅ 成功載入 {len(self.expected_sites)} 個預期站點")
        except FileNotFoundError:
            print(f"❌ 找不到檔案: {self.expected_file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ 載入原始資料失敗: {e}", file=sys.stderr)
            sys.exit(1)

    def _clean(self, text: str) -> str:
        if not text:
            return ''
        text = unicodedata.normalize('NFKC', text)  # 全形→半形
        text = re.sub(r'\s+', '', text)              # 移除所有空白
        return text

    def _compare(self) -> Tuple[List[Dict], List[Dict]]:
        """比對站點差異"""
        print("🔍 正在比對站點...")
        
        new_sites = self.api_sites - self.expected_sites
        removed_sites = self.expected_sites - self.api_sites
        
        new_sites_list = [
            {'siteid': s[0], 'sitename': s[1], 'county': s[2]}
            for s in sorted(new_sites, key=lambda x: x[0])
        ]
        
        removed_sites_list = [
            {'siteid': s[0], 'sitename': s[1], 'county': s[2]}
            for s in sorted(removed_sites, key=lambda x: x[0])
        ]
        
        return new_sites_list, removed_sites_list

    def _generate_report(self, new_sites: List[Dict], removed_sites: List[Dict]) -> Dict:
        """生成比對報告"""
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'has_changes': bool(new_sites or removed_sites),
            'statistics': {
                'api_total': len(self.api_sites),
                'expected_total': len(self.expected_sites),
                'new_count': len(new_sites),
                'removed_count': len(removed_sites)
            },
            'new_sites': new_sites,
            'removed_sites': removed_sites
        }
        return report

    def _print_summary(self, report: Dict) -> None:
        """輸出摘要到終端"""
        print("\n" + "="*60)
        print(f"📊 比對結果摘要 ({report['timestamp']})")
        print("="*60)
        print(f"API 站點總數: {report['statistics']['api_total']}")
        print(f"預期站點總數: {report['statistics']['expected_total']}")
        print(f"新增站點數: {report['statistics']['new_count']}")
        print(f"移除站點數: {report['statistics']['removed_count']}")
        
        if report['new_sites']:
            print("\n🆕 新增站點:")
            for site in report['new_sites']:
                print(f"  - {site['siteid']}: {site['sitename']} ({site['county']})")
        
        if report['removed_sites']:
            print("\n❌ 移除站點:")
            for site in report['removed_sites']:
                print(f"  - {site['siteid']}: {site['sitename']} ({site['county']})")
        
        if not report['has_changes']:
            print("\n✅ 無站點變更")
        
        print("="*60)

    def _generate_github_summary(self, report: Dict) -> None:
        """生成 GitHub Actions Summary"""
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
        if not summary_file:
            print("⚠️ 非 GitHub Actions 環境,跳過 Summary 生成")
            return
        
        print("📝 正在生成 GitHub Summary...")
        
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write("## 🔍 站點變更檢查結果\n\n")
            f.write(f"**檢查時間:** {report['timestamp']}\n\n")
            
            if report['has_changes']:
                f.write("### ⚠️ 偵測到站點變更\n\n")
                
                if report['new_sites']:
                    f.write("#### 🆕 新增站點:\n\n")
                    for site in report['new_sites']:
                        f.write(f"- **{site['siteid']}**: {site['sitename']} ({site['county']})\n")
                    f.write("\n")
                
                if report['removed_sites']:
                    f.write("#### ❌ 移除站點:\n\n")
                    for site in report['removed_sites']:
                        f.write(f"- **{site['siteid']}**: {site['sitename']} ({site['county']})\n")
                    f.write("\n")
            else:
                f.write("### ✅ 無站點變更\n\n")
                f.write("所有站點與預期相符,未偵測到任何變更。\n\n")
            
            f.write("---\n\n")
            f.write("📊 **統計資訊:**\n\n")
            f.write(f"- API 回傳站點數: {report['statistics']['api_total']}\n")
            f.write(f"- 預期站點數: {report['statistics']['expected_total']}\n")
            f.write(f"- 新增站點數: {report['statistics']['new_count']}\n")
            f.write(f"- 移除站點數: {report['statistics']['removed_count']}\n")
        
        print("✅ GitHub Summary 已生成")

    def _build_issue_body(self, report: Dict) -> str:
        """生成issue body"""
        def _render_sites(sites):
            return "\n".join(
                f"- {s['siteid']}: {s['sitename']} ({s['county']})"
                for s in sites
            )

        parts = ["# 🚨 Changes Detected in Site list:\n"]

        if not report['has_changes']:
            parts += [
                "### ✅ 無站點變更\n",
                "所有站點與預期相符,未偵測到任何變更。\n"
            ]
        else:
            if report['new_sites']:
                parts += [
                    "### 🆕 New Sites:\n",
                    _render_sites(report['new_sites']),
                    ""
                ]

            if report['removed_sites']:
                parts += [
                    "### ❌ Removed Sites:\n",
                    _render_sites(report['removed_sites']),
                    ""
                ]

            parts.append("@kukuxx\n")

        parts.append(f"---\n\n**檢查時間:** {report['timestamp']}")

        return "\n".join(parts)

    def _create_or_update_issue(self, report: Dict) -> None:
        """建立或更新 GitHub Issue"""
        try:
            print("🔔 正在處理 GitHub Issue...")

            gh_token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
            if not gh_token:
                raise RuntimeError("⚠️ 找不到 GitHub Token,跳過 Issue 建立")

            body = self._build_issue_body(report)
            
            # 檢查是否已有相同標籤的 Issue
            result = subprocess.run(
                ['gh', 'issue', 'list', '--state', 'open', '--label', 'site change', '--json', 'number'],
                capture_output=True,
                text=True,
                check=True
            )
            
            issues = json.loads(result.stdout)
            
            if issues:
                issue_number = issues[0]['number']
                print(f"✏️ 更新現有 Issue: #{issue_number}")
                subprocess.run(
                    ['gh', 'issue', 'edit', str(issue_number), '--body', body],
                    check=True
                )
            else:
                print("🆕 建立新 Issue")
                subprocess.run(
                    ['gh', 'issue', 'create', '--title', 'Site change', '--body', body, '--label', 'site change'],
                    check=True
                )
            
            print("✅ Issue 處理完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ 處理 Issue 失敗: {e}", file=sys.stderr)
        except FileNotFoundError:
            print("❌ 找不到 gh 指令,請確認已安裝 GitHub CLI", file=sys.stderr)
        except Exception as e:
            print(f"❌ 處理 Issue 失敗: {e}")

    def run(self) -> Dict:
        """執行完整的比對流程"""
        self._fetch_api_data()
        self._load_expected_data()
        new_sites, removed_sites = self._compare()
        report = self._generate_report(new_sites, removed_sites)
        self._print_summary(report)
        self._generate_github_summary(report)
        self._create_or_update_issue(report)
        return report


def main():
    api_url = "https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key=e75b1660-e564-4107-aad5-a8be1f905dd9&sort=ImportDate%20desc&format=CSV"
    
    expected_file = "asset/aqx_p_432.csv"
    
    comparator = SiteComparator(api_url, expected_file)
    report = comparator.run()
    
    if report['has_changes']:
        print("\n⚠️ 偵測到變更")
        sys.exit(0)
    else:
        print("\n✅ 無變更")
        sys.exit(0)


if __name__ == "__main__":
    main()