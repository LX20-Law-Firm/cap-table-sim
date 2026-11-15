"use strict";
const CapTable = (() => {
  function gcd(a,b) { a=a<0n?-a:a; b=b<0n?-b:b; while(b){[a,b]=[b,a%b];} return a; }
  class R {
    constructor(n,d=1n) { if(d===0n)throw Error("Division by zero");if(d<0n){n=-n;d=-d;}const g=gcd(n,d);this.n=n/g;this.d=d/g; }
    add(b){return new R(this.n*b.d+b.n*this.d,this.d*b.d);}
    sub(b){return new R(this.n*b.d-b.n*this.d,this.d*b.d);}
    mul(b){return new R(this.n*b.n,this.d*b.d);}
    div(b){return new R(this.n*b.d,this.d*b.n);}
    lt(b){return this.n*b.d<b.n*this.d;}
    toString(){return this.d===1n?String(this.n):`${this.n}/${this.d}`;}
  }
  const zero=new R(0n), one=new R(1n);
  function q(x, positive=false) {
    if (typeof x === "number" && !Number.isSafeInteger(x)) throw Error("Use decimal strings for fractional inputs");
    if (typeof x!=="string" && typeof x!=="number") throw Error("Use decimal strings or integers");
    if(!/^\d+(?:\.\d+)?$/.test(String(x))) throw Error("Invalid non-negative decimal");
    const [whole,part=""]=String(x).split(".");const r=new R(BigInt(whole+part),10n**BigInt(part.length));
    if(positive && r.n===0n)throw Error("Value must be positive");return r;
  }
  function minimum(a,b){return a.lt(b)?a:b;}
  function maximum(a,b){return a.lt(b)?b:a;}
  function sum(xs){return xs.reduce((a,b)=>a.add(b),zero);}
  function round(x,step){if(!step)return x;const units=x.div(step);return new R(units.n/units.d).mul(step);}
  function name(x){if(typeof x!=="string"||!x||x==="Employee pool")throw Error("Invalid holder name");return x;}
  function calculate(x) {
    if(!x.holdings || typeof x.holdings!=="object" || Array.isArray(x.holdings))throw Error("Provide holdings");
    const owners=Object.create(null);
    for(const [holder,value] of Object.entries(x.holdings)){if(!holder)throw Error("Missing holder name");owners[holder]=q(value);}
    const base=sum(Object.values(owners));if(base.n===0n)throw Error("Existing units must be positive");
    const v=q(x.pre_money,true), cash=q(x.investment), target=q(x.pool_target??"0");
    const timing=x.pool_timing??"pre", unit=x.unit??"SPA shares", investor=name(x.investor??"New investor");
    if(!["pre","post"].includes(timing)||!target.lt(one))throw Error("Invalid pool inputs");
    if(!["SPA shares","SRL quota units"].includes(unit))throw Error("Invalid unit");
    const step=x.quantum==null?null:q(x.quantum,true);
    if(step && Object.values(owners).some(value=>value.div(step).d!==1n))throw Error("Holdings must be multiples of quantum");
    const instruments=x.instruments??[];
    if(!Array.isArray(instruments))throw Error("Instruments must be an array");
    const terms=instruments.map(i=>{
      name(i.holder);const principal=q(i.principal),d=q(i.discount??"0"),r=q(i.annual_interest??"0"),t=q(i.years??"0"),kind=i.kind??"safe";
      if(!d.lt(one)||!["safe","note"].includes(kind))throw Error("Invalid instrument");
      if(kind==="safe"&&(r.n||t.n))throw Error("SAFE inputs cannot accrue interest");
      const amount=principal.mul(one.add(r.mul(t)));
      const numerator=minimum(v.mul(one.sub(d)),i.cap==null?v:q(i.cap,true));
      return {holder:i.holder,amount,numerator};
    });
    const existing=owners["Employee pool"]??zero;let added=zero;
    if(timing==="pre"){
      const factor=one.add(cash.div(v)).add(sum(terms.map(t=>t.amount.div(t.numerator))));
      const denominator=one.sub(target.mul(factor));
      if(!zero.lt(denominator))throw Error("Pool target cannot be reached under this pre-money model");
      added=round(maximum(zero,target.mul(factor).mul(base).sub(existing).div(denominator)),step);
    }
    const capitalization=base.add(added), price=v.div(capitalization);
    const conversions=terms.map(t=>{
      const p=t.numerator.div(capitalization),units=round(t.amount.div(p),step);
      owners[t.holder]=(owners[t.holder]??zero).add(units);
      return {holder:t.holder,price:p.toString(),units:units.toString(),unconverted_amount:t.amount.sub(units.mul(p)).toString()};
    });
    const issued=round(cash.div(price),step);owners[investor]=(owners[investor]??zero).add(issued);
    if(timing==="post")added=round(maximum(zero,target.mul(sum(Object.values(owners))).sub(existing).div(one.sub(target))),step);
    if(existing.n||added.n)owners["Employee pool"]=existing.add(added);
    const total=sum(Object.values(owners));
    return {holdings:Object.fromEntries(Object.entries(owners).map(([h,n])=>[h,n.toString()])),
      ownership:Object.fromEntries(Object.entries(owners).map(([h,n])=>[h,n.div(total).toString()])),
      round_price:price.toString(),pool_added:added.toString(),pool_fraction:(owners["Employee pool"]??zero).div(total).toString(),
      new_investor_units:issued.toString(),unallocated_cash:cash.sub(issued.mul(price)).toString(),conversions,unit};
  }
  return {calculate};
})();
if(typeof module!=="undefined")module.exports=CapTable;
