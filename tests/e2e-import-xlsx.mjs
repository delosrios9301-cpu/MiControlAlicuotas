import { strict as assert } from 'node:assert';
import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,serviceWorkers:'block'});
const errors=[],logs=[];
page.on('pageerror',e=>errors.push(String(e.message)));
page.on('console',msg=>{if(msg.type()==='error')logs.push(msg.text());});
page.on('dialog',dialog=>dialog.accept());
try {
 await page.goto('http://127.0.0.2:8765/',{waitUntil:'domcontentloaded',timeout:30000});
 await page.waitForTimeout(1200);
 // La navegación de la app usa data-page en el menú; en móvil puede estar oculto.
 const found=await page.locator('[data-page="mi-excel"]').count();
 assert.ok(found,'Falta entrada Mi Excel en la app');
 await page.locator('[data-page="mi-excel"]').first().evaluate(e=>e.click());
 const selector=page.locator('#manualExcelInput');
 await selector.waitFor({state:'attached',timeout:15000});
 const fake=await readFile('tests/prueba_xlsx_ficticia.xlsx');
 await selector.setInputFiles({name:'prueba_xlsx_ficticia.xlsx',mimeType:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',buffer:fake});
 await page.waitForTimeout(2200);
 const result=await page.locator('#excelImportResult').innerText().catch(()=>'<sin sección resultado>');
 const sync=await page.locator('[data-page="sincronizacion"]').first().evaluate(e=>e.click()).then(async()=>await page.locator('main').innerText().catch(()=>document.body.innerText())).catch(()=>'<sin navegación>');
 const modal=await page.locator('#modalRoot').innerText().catch(()=>'');
 console.log('E2E_RESULTADO:',result.slice(0,1100));
 console.log('E2E_MODAL:',modal.slice(0,900));
 console.log('E2E_SYNC:',sync.slice(0,1700));
 console.log('E2E_JS_ERRORS:',errors);
 console.log('E2E_CONSOLE_ERRORS:',logs);
 assert.ok(sync.includes('Capturador de Windows (equipo separado)'),'En móvil se muestran instrucciones erróneas de PC');
 assert.ok(sync.includes('Capturas Excel para revisar'),'No se muestra lista de capturas Excel');
 assert.ok(sync.includes('Capturas XLSX guardadas en este dispositivo:'),'No se diferencian capturas locales de filas compartidas Firebase');
 assert.ok(sync.includes('Cuenta Firebase sin sesión'),'Se muestra Firebase conectado sin autenticar');
 assert.ok(result.includes('Filas de Excel guardadas localmente'),'No se informa resultado de importación');
 assert.ok(result.includes('2'),'No aparecen las dos filas ficticias en el resultado');
 assert.ok(!errors.length,'La aplicación tuvo errores de ejecución: '+errors.join('; '));
 // Debe conservar los datos incluso tras refrescar la página.
 await page.reload({waitUntil:'domcontentloaded'});
 await page.waitForTimeout(700);
 await page.locator('[data-page="mi-excel"]').first().evaluate(e=>e.click());
 const retained=await page.locator('#excelImportResult').innerText();
 console.log('E2E_PERSISTENCIA:',retained.slice(0,700));
 assert.ok(retained.includes('2'),'Las capturas se perdieron tras refrescar la aplicación');
 console.log('E2E OK: importación, visualización y persistencia de 2 registros ficticios');
} finally {await browser.close();}
