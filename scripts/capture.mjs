import { chromium, devices } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
const base=process.env.DEMO_URL||'http://127.0.0.1:4175/';
await mkdir('docs',{recursive:true});
const browser=await chromium.launch();
try{
 for(const [name,options] of [['explorer',{viewport:{width:1440,height:1050},deviceScaleFactor:1}],['mobile',{...devices['Pixel 7'],deviceScaleFactor:1}]]){
  const context=await browser.newContext(options),page=await context.newPage();await page.goto(base);await page.locator('#activation-count').filter({hasText:'ACTIVE'}).waitFor();
  await page.screenshot({path:`docs/${name}.png`,fullPage:true});
  if(name==='explorer'){await page.getByRole('button',{name:'Evaluation',exact:true}).click();await page.locator('#metric-cards article').last().waitFor();await page.screenshot({path:'docs/evaluation.png',fullPage:true});}
  await context.close();
 }
}finally{await browser.close();}
console.log('Saved desktop, mobile, and evaluation screenshots.');
