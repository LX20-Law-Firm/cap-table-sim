const {test}=require('node:test');
const assert=require('node:assert/strict');
const {calculate}=require('../docs/calculator.js');
const base={holdings:{Founder:'1000'},pre_money:'10000',investment:'2500',pool_target:'0.2'};
test('pre and post pools with exact fractions',()=>{
 const pre=calculate(base),post=calculate({...base,pool_timing:'post'});
 assert.equal(pre.pool_added,'1000/3');assert.equal(pre.round_price,'15/2');
 assert.equal(pre.pool_fraction,'1/5');assert.equal(pre.ownership['New investor'],'1/5');
 assert.equal(post.pool_added,'625/2');assert.equal(post.ownership['New investor'],'4/25');
});
test('simultaneous conversion and interest',()=>{
 const result=calculate({...base,pool_target:'0',instruments:[{holder:'A',principal:'1000',cap:'5000',discount:'0.2'},
 {holder:'B',principal:'1000',discount:'0.2',kind:'note',annual_interest:'0.1',years:'2'}]});
 assert.equal(result.holdings.A,'200');assert.equal(result.holdings.B,'150');
});
test('rounding residuals and unsafe inputs',()=>{
 const result=calculate({holdings:{Founder:'3'},pre_money:'10',investment:'1',quantum:'1'});
 assert.equal(result.unallocated_cash,'1');assert.equal(result.new_investor_units,'0');
 assert.equal(calculate({...base,quantum:'1'}).pool_added,'333');
 assert.throws(()=>calculate({...base,pool_target:'0.99'}));
 assert.throws(()=>calculate({...base,quantum:'0'}));
 assert.throws(()=>calculate({...base,pre_money:'NaN'}));
});
