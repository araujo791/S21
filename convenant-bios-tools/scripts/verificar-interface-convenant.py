#!/usr/bin/env python3
"""Optional Playwright check of an already-running local app; never touches hardware."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--second', type=Path, required=True)
    parser.add_argument('--corrupted', type=Path, required=True)
    parser.add_argument('--screenshots', type=Path, required=True)
    parser.add_argument('--chromium', default='/usr/bin/chromium')
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright, expect
    args.screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium, headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]
        page.on('pageerror', lambda err: errors.append(str(err)))
        page.goto(args.url, wait_until='networkidle')
        expect(page.locator('#board')).not_to_have_text('Consultando…')
        assert page.title() == 'Convenant BIOS Tools'
        page.screenshot(path=str(args.screenshots/'overview.png'),full_page=True)
        for name in ('backups','microcodes','write','settings','analysis'):
            page.locator('[data-tab="'+name+'"]').click()
            assert page.locator('#'+name).is_visible()
        assert page.locator('#open-confirm').is_disabled()
        page.locator('#upload').set_input_files([str(args.base),str(args.second),str(args.corrupted)])
        page.locator('body:not(.busy)').wait_for()
        def select_file(selector,path):
            options=page.locator(selector+' option').evaluate_all('(nodes)=>nodes.map(n=>({value:n.value,text:n.textContent}))')
            match=next(v for v in options if v['text'].startswith(path.name+' ·'))
            page.locator(selector).select_option(match['value'])
        def finish():
            page.locator('body:not(.busy)').wait_for(timeout=120000)
            return json.loads(page.locator('#result-json').text_content())
        select_file('#analysis-file',args.base)
        page.locator('#analyze').click()
        good=finish()
        assert good['profile']=='002-original' and good['deep']['passed'] and not good['issues']
        page.screenshot(path=str(args.screenshots/'analysis-good.png'),full_page=True)
        select_file('#compare-first',args.base);select_file('#compare-second',args.second)
        page.locator('#compare').click();same=finish()
        assert same['identical'] and same['whole']['different_bytes']==0
        select_file('#analysis-file',args.corrupted);page.locator('#analyze').click();bad=finish()
        assert bad['issues'] and not bad['deep']['passed']
        page.screenshot(path=str(args.screenshots/'analysis-errors.png'),full_page=True)
        select_file('#compare-second',args.corrupted);page.locator('#compare').click();changed=finish()
        assert changed['code_excluding_first_512KiB_nvram']['different_bytes']>0
        page.reload(wait_until='networkidle')
        page.locator('[data-tab="settings"]').click()
        page.wait_for_selector('.file-item')
        assert page.locator('.file-item').count()>=3
        page.set_viewport_size({'width':390,'height':844})
        page.locator('[data-tab="overview"]').click()
        assert page.locator('#overview').is_visible()
        assert page.evaluate('() => document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(args.screenshots/'mobile.png'),full_page=True)
        assert not errors,errors
        browser.close()
    print(json.dumps({'browser':'Chromium','checks':['navigation','upload','valid_firmware_analysis','identical_comparison','corrupted_firmware_detection','different_comparison','persisted_files','responsive_layout'],'hardware_accessed':False,'javascript_errors':errors},indent=2))


if __name__=='__main__':
    main()
