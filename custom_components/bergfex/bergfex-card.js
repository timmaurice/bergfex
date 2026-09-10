function t(t,e,s,i){var o,n=arguments.length,a=n<3?e:null===i?i=Object.getOwnPropertyDescriptor(e,s):i;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)a=Reflect.decorate(t,e,s,i);else for(var r=t.length-1;r>=0;r--)(o=t[r])&&(a=(n<3?o(a):n>3?o(e,s,a):o(e,s))||a);return n>3&&a&&Object.defineProperty(e,s,a),a}console.groupCollapsed("%c🏔️ BERGFEX CARD%cv3.0.0","color: orange; font-weight: bold; background: black; padding: 2px 4px; border-radius: 2px 0 0 2px;","color: white; font-weight: bold; background: dimgray; padding: 2px 4px; border-radius: 0 2px 2px 0;"),console.info("A Lovelace card to display ski resort conditions from Bergfex."),console.info("Github:  https://github.com/timmaurice/bergfex.git"),console.info("Sponsor: https://buymeacoffee.com/timmaurice"),console.groupEnd(),"function"==typeof SuppressedError&&SuppressedError;
/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const e=globalThis,s=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),o=new WeakMap;let n=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(s&&void 0===t){const s=void 0!==e&&1===e.length;s&&(t=o.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&o.set(e,t))}return t}toString(){return this.cssText}};const a=t=>new n("string"==typeof t?t:t+"",void 0,i),r=(t,...e)=>{const s=1===t.length?t[0]:e.reduce((e,s,i)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[i+1],t[0]);return new n(s,t,i)},c=s?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return a(e)})(t):t,{is:l,defineProperty:d,getOwnPropertyDescriptor:h,getOwnPropertyNames:p,getOwnPropertySymbols:u,getPrototypeOf:_}=Object,f=globalThis,m=f.trustedTypes,g=m?m.emptyScript:"",v=f.reactiveElementPolyfillSupport,y=(t,e)=>t,w={toAttribute(t,e){switch(e){case Boolean:t=t?g:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let s=t;switch(e){case Boolean:s=null!==t;break;case Number:s=null===t?null:Number(t);break;case Object:case Array:try{s=JSON.parse(t)}catch(t){s=null}}return s}},b=(t,e)=>!l(t,e),$={attribute:!0,type:String,converter:w,reflect:!1,useDefault:!1,hasChanged:b};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */Symbol.metadata??=Symbol("metadata"),f.litPropertyMetadata??=new WeakMap;let k=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=$){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const s=Symbol(),i=this.getPropertyDescriptor(t,s,e);void 0!==i&&d(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){const{get:i,set:o}=h(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:i,set(e){const n=i?.call(this);o?.call(this,e),this.requestUpdate(t,n,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??$}static _$Ei(){if(this.hasOwnProperty(y("elementProperties")))return;const t=_(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(y("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(y("properties"))){const t=this.properties,e=[...p(t),...u(t)];for(const s of e)this.createProperty(s,t[s])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,s]of e)this.elementProperties.set(t,s)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const s=this._$Eu(t,e);void 0!==s&&this._$Eh.set(s,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const s=new Set(t.flat(1/0).reverse());for(const t of s)e.unshift(c(t))}else void 0!==t&&e.push(c(t));return e}static _$Eu(t,e){const s=e.attribute;return!1===s?void 0:"string"==typeof s?s:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,i)=>{if(s)t.adoptedStyleSheets=i.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const s of i){const i=document.createElement("style"),o=e.litNonce;void 0!==o&&i.setAttribute("nonce",o),i.textContent=s.cssText,t.appendChild(i)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){const s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(void 0!==i&&!0===s.reflect){const o=(void 0!==s.converter?.toAttribute?s.converter:w).toAttribute(e,s.type);this._$Em=t,null==o?this.removeAttribute(i):this.setAttribute(i,o),this._$Em=null}}_$AK(t,e){const s=this.constructor,i=s._$Eh.get(t);if(void 0!==i&&this._$Em!==i){const t=s.getPropertyOptions(i),o="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:w;this._$Em=i;const n=o.fromAttribute(e,t.type);this[i]=n??this._$Ej?.get(i)??n,this._$Em=null}}requestUpdate(t,e,s,i=!1,o){if(void 0!==t){const n=this.constructor;if(!1===i&&(o=this[t]),s??=n.getPropertyOptions(t),!((s.hasChanged??b)(o,e)||s.useDefault&&s.reflect&&o===this._$Ej?.get(t)&&!this.hasAttribute(n._$Eu(t,s))))return;this.C(t,e,s)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:o},n){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,n??e??this[t]),!0!==o||void 0!==n)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),!0===i&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,s]of t){const{wrapped:t}=s,i=this[e];!0!==t||this._$AL.has(e)||void 0===i||this.C(e,void 0,s,i)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};k.elementStyles=[],k.shadowRootOptions={mode:"open"},k[y("elementProperties")]=new Map,k[y("finalized")]=new Map,v?.({ReactiveElement:k}),(f.reactiveElementVersions??=[]).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const x=globalThis,S=t=>t,A=x.trustedTypes,N=A?A.createPolicy("lit-html",{createHTML:t=>t}):void 0,C="$lit$",E=`lit$${Math.random().toFixed(9).slice(2)}$`,P="?"+E,T=`<${P}>`,j=document,z=()=>j.createComment(""),O=t=>null===t||"object"!=typeof t&&"function"!=typeof t,M=Array.isArray,R="[ \t\n\f\r]",D=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,L=/-->/g,U=/>/g,F=RegExp(`>|${R}(?:([^\\s"'>=/]+)(${R}*=${R}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),I=/'/g,B=/"/g,H=/^(?:script|style|textarea|title)$/i,W=(t=>(e,...s)=>({_$litType$:t,strings:e,values:s}))(1),V=Symbol.for("lit-noChange"),q=Symbol.for("lit-nothing"),G=new WeakMap,K=j.createTreeWalker(j,129);function Z(t,e){if(!M(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==N?N.createHTML(e):e}const J=(t,e)=>{const s=t.length-1,i=[];let o,n=2===e?"<svg>":3===e?"<math>":"",a=D;for(let e=0;e<s;e++){const s=t[e];let r,c,l=-1,d=0;for(;d<s.length&&(a.lastIndex=d,c=a.exec(s),null!==c);)d=a.lastIndex,a===D?"!--"===c[1]?a=L:void 0!==c[1]?a=U:void 0!==c[2]?(H.test(c[2])&&(o=RegExp("</"+c[2],"g")),a=F):void 0!==c[3]&&(a=F):a===F?">"===c[0]?(a=o??D,l=-1):void 0===c[1]?l=-2:(l=a.lastIndex-c[2].length,r=c[1],a=void 0===c[3]?F:'"'===c[3]?B:I):a===B||a===I?a=F:a===L||a===U?a=D:(a=F,o=void 0);const h=a===F&&t[e+1].startsWith("/>")?" ":"";n+=a===D?s+T:l>=0?(i.push(r),s.slice(0,l)+C+s.slice(l)+E+h):s+E+(-2===l?e:h)}return[Z(t,n+(t[s]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),i]};class Y{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let o=0,n=0;const a=t.length-1,r=this.parts,[c,l]=J(t,e);if(this.el=Y.createElement(c,s),K.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(i=K.nextNode())&&r.length<a;){if(1===i.nodeType){if(i.hasAttributes())for(const t of i.getAttributeNames())if(t.endsWith(C)){const e=l[n++],s=i.getAttribute(t).split(E),a=/([.?@])?(.*)/.exec(e);r.push({type:1,index:o,name:a[2],strings:s,ctor:"."===a[1]?st:"?"===a[1]?it:"@"===a[1]?ot:et}),i.removeAttribute(t)}else t.startsWith(E)&&(r.push({type:6,index:o}),i.removeAttribute(t));if(H.test(i.tagName)){const t=i.textContent.split(E),e=t.length-1;if(e>0){i.textContent=A?A.emptyScript:"";for(let s=0;s<e;s++)i.append(t[s],z()),K.nextNode(),r.push({type:2,index:++o});i.append(t[e],z())}}}else if(8===i.nodeType)if(i.data===P)r.push({type:2,index:o});else{let t=-1;for(;-1!==(t=i.data.indexOf(E,t+1));)r.push({type:7,index:o}),t+=E.length-1}o++}}static createElement(t,e){const s=j.createElement("template");return s.innerHTML=t,s}}function Q(t,e,s=t,i){if(e===V)return e;let o=void 0!==i?s._$Co?.[i]:s._$Cl;const n=O(e)?void 0:e._$litDirective$;return o?.constructor!==n&&(o?._$AO?.(!1),void 0===n?o=void 0:(o=new n(t),o._$AT(t,s,i)),void 0!==i?(s._$Co??=[])[i]=o:s._$Cl=o),void 0!==o&&(e=Q(t,o._$AS(t,e.values),o,i)),e}class X{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??j).importNode(e,!0);K.currentNode=i;let o=K.nextNode(),n=0,a=0,r=s[0];for(;void 0!==r;){if(n===r.index){let e;2===r.type?e=new tt(o,o.nextSibling,this,t):1===r.type?e=new r.ctor(o,r.name,r.strings,this,t):6===r.type&&(e=new nt(o,this,t)),this._$AV.push(e),r=s[++a]}n!==r?.index&&(o=K.nextNode(),n++)}return K.currentNode=j,i}p(t){let e=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}}class tt{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=q,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Q(this,t,e),O(t)?t===q||null==t||""===t?(this._$AH!==q&&this._$AR(),this._$AH=q):t!==this._$AH&&t!==V&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>M(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==q&&O(this._$AH)?this._$AA.nextSibling.data=t:this.T(j.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:s}=t,i="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=Y.createElement(Z(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{const t=new X(i,this),s=t.u(this.options);t.p(e),this.T(s),this._$AH=t}}_$AC(t){let e=G.get(t.strings);return void 0===e&&G.set(t.strings,e=new Y(t)),e}k(t){M(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let s,i=0;for(const o of t)i===e.length?e.push(s=new tt(this.O(z()),this.O(z()),this,this.options)):s=e[i],s._$AI(o),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=S(t).nextSibling;S(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class et{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,o){this.type=1,this._$AH=q,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=o,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=q}_$AI(t,e=this,s,i){const o=this.strings;let n=!1;if(void 0===o)t=Q(this,t,e,0),n=!O(t)||t!==this._$AH&&t!==V,n&&(this._$AH=t);else{const i=t;let a,r;for(t=o[0],a=0;a<o.length-1;a++)r=Q(this,i[s+a],e,a),r===V&&(r=this._$AH[a]),n||=!O(r)||r!==this._$AH[a],r===q?t=q:t!==q&&(t+=(r??"")+o[a+1]),this._$AH[a]=r}n&&!i&&this.j(t)}j(t){t===q?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class st extends et{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===q?void 0:t}}class it extends et{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==q)}}class ot extends et{constructor(t,e,s,i,o){super(t,e,s,i,o),this.type=5}_$AI(t,e=this){if((t=Q(this,t,e,0)??q)===V)return;const s=this._$AH,i=t===q&&s!==q||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,o=t!==q&&(s===q||i);i&&this.element.removeEventListener(this.name,this,s),o&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class nt{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){Q(this,t)}}const at=x.litHtmlPolyfillSupport;at?.(Y,tt),(x.litHtmlVersions??=[]).push("3.3.3");const rt=globalThis;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */let ct=class extends k{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,s)=>{const i=s?.renderBefore??e;let o=i._$litPart$;if(void 0===o){const t=s?.renderBefore??null;i._$litPart$=o=new tt(e.insertBefore(z(),t),t,void 0,s??{})}return o._$AI(t),o})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return V}};ct._$litElement$=!0,ct.finalized=!0,rt.litElementHydrateSupport?.({LitElement:ct});const lt=rt.litElementPolyfillSupport;lt?.({LitElement:ct}),(rt.litElementVersions??=[]).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const dt={attribute:!0,type:String,converter:w,reflect:!1,hasChanged:b},ht=(t=dt,e,s)=>{const{kind:i,metadata:o}=s;let n=globalThis.litPropertyMetadata.get(o);if(void 0===n&&globalThis.litPropertyMetadata.set(o,n=new Map),"setter"===i&&((t=Object.create(t)).wrapped=!0),n.set(s.name,t),"accessor"===i){const{name:i}=s;return{set(s){const o=e.get.call(this);e.set.call(this,s),this.requestUpdate(i,o,t,!0,s)},init(e){return void 0!==e&&this.C(i,void 0,t,e),e}}}if("setter"===i){const{name:i}=s;return function(s){const o=this[i];e.call(this,s),this.requestUpdate(i,o,t,!0,s)}}throw Error("Unsupported decorator location: "+i)};function pt(t){return(e,s)=>"object"==typeof s?ht(t,e,s):((t,e,s)=>{const i=e.hasOwnProperty(s);return e.constructor.createProperty(s,t),i?Object.getOwnPropertyDescriptor(e,s):void 0})(t,e,s)}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function ut(t){return pt({...t,state:!0,attribute:!1})}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const _t={show_snow:!0,show_lifts_slopes:!0,show_trails:!0,show_conditions:!0,show_forecast:!1,show_trend:!1,show_link:!0,show_last_updated:!0,hide_closed_resorts:!1,conditions_default_open:!1,forecast_default_open:!1};function ft(t){const e={...t};for(const[t,s]of Object.entries(_t))e[t]===s&&delete e[t];for(const t of["title","sort_by"]){const s=e[t];void 0!==s&&""!==s&&"none"!==s||delete e[t]}return e}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const mt=1,gt=2,vt=t=>(...e)=>({_$litDirective$:t,values:e});class yt{constructor(t){}get _$AU(){return this._$AM._$AU}_$AT(t,e,s){this._$Ct=t,this._$AM=e,this._$Ci=s}_$AS(t,e){return this.update(t,e)}update(t,e){return this.render(...e)}}
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const wt=vt(class extends yt{constructor(t){if(super(t),t.type!==mt||"class"!==t.name||t.strings?.length>2)throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.")}render(t){return" "+Object.keys(t).filter(e=>t[e]).join(" ")+" "}update(t,[e]){if(void 0===this.st){this.st=new Set,void 0!==t.strings&&(this.nt=new Set(t.strings.join(" ").split(/\s/).filter(t=>""!==t)));for(const t in e)e[t]&&!this.nt?.has(t)&&this.st.add(t);return this.render(e)}const s=t.element.classList;for(const t of this.st)t in e||(s.remove(t),this.st.delete(t));for(const t in e){const i=!!e[t];i===this.st.has(t)||this.nt?.has(t)||(i?(s.add(t),this.st.add(t)):(s.remove(t),this.st.delete(t)))}return V}});
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */class bt extends yt{constructor(t){if(super(t),this.it=q,t.type!==gt)throw Error(this.constructor.directiveName+"() can only be used in child bindings")}render(t){if(t===q||null==t)return this._t=void 0,this.it=t;if(t===V)return t;if("string"!=typeof t)throw Error(this.constructor.directiveName+"() called with a non-string value");if(t===this.it)return this._t;this.it=t;const e=[t];return e.raw=e,this._t={_$litType$:this.constructor.resultType,strings:e,values:[]}}}bt.directiveName="unsafeHTML",bt.resultType=1;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
class $t extends bt{}$t.directiveName="unsafeSVG",$t.resultType=2;const kt=vt($t);const xt={da:{editor:{groups:{core:"Kerne Konfiguration",display:"Visning",ski_only:"Skiområde muligheder",cross_country_only:"Indstillinger for langrend"},title:"Title (Valgfri)",resorts:"Område enheder",show_snow:"Vis sne information",show_lifts_slopes:"Vis lift & piste statistik",show_conditions:"Vis forholds sektion",conditions_default_open:"Forholds sektion udvidet som standard",show_forecast:"Vis sne udsigt",forecast_default_open:"Sne udsigt udvidet som standard",show_trend:"Vis trend indikatorer (24h)",show_last_updated:"Vis sidst opdateret",show_link:"Vis link ikon",hide_closed_resorts:"Skjul lukkede områder",hide_closed_resorts_helper:"Skjuler kun skisportssteder mellem vinter- og sommersæsonen. Steder i sommerdrift forbliver synlige, selv om man ikke kan stå på ski.",sort_by:"Sorter efter",sort_by_options:{mountain:"Sne (Bjerg)",valley:"Sne (Dal)",new:"Ny sne",lift:"Lifter åbne",classical:"Klassiske stier",skating:"Skate stier",update:"Sidste opdatering"},show_trails:"Vis løjpestatistik"},card:{resort_not_found:"Områder ikke fundet: {resort}",lifts_open:"Lifter",header:{snow_mountain:"Bjerg",snow_valley:"Dal",new_snow:"Ny",snow_condition:"Sne forhold",slope_condition:"Piste forhold",avalanche_warning:"Lavine advarsel",last_snowfall:"Sidste snefald",slopes_info:"Pister",slopes_info_km:"Pister (km)",slopes_open_km:"Åben",slopes_total:"Total",classical_trails:"Klassiske stier",skating_trails:"Skate stier",classical_condition:"Klassisk forhold",skating_condition:"Skate forhold",operation_status:"Driftsstatus",link_title:"Åben {resortName} detaljeret side på bergfex"},forecast:{daily:"Daglig",summary:"Opsummeret",hour:"{hours} Timer",today:"I dag",tomorrow:"I morgen"},accordion:{conditions:"Forhold",forecast:"Sne udsigt"},status:{open:"Åben",closed:"Lukket",unknown:"Ukendt",winter_season:"Vintersæson",summer_season:"Sommersæson",season_from:"fra {date}",season_last_year:"sidste år: {date}"},warnings:{not_found:"Skisportsstedet blev ikke fundet: {subject}",unavailable:"Der rapporteres ingen data for {subject}.",wrong_domain:"{subject} er en {actual}-enhed, men der kræves en {expected}.",not_numeric:'{subject} rapporterer ikke et tal (værdien er "{state}").'}},common:{errors:{no_resorts:"Du skal definere mindst én feriestedsenhed."}}},de:{editor:{groups:{core:"Grundeinstellungen",display:"Anzeige",ski_only:"Optionen für Skigebiete",cross_country_only:"Optionen für Loipengebiete"},title:"Titel (Optional)",resorts:"Skigebiete",show_snow:"Schneeinformationen anzeigen",show_lifts_slopes:"Lift- & Pistenstatistiken anzeigen",show_conditions:"Bedingungen anzeigen",conditions_default_open:"Bedingungen standardmäßig ausgeklappt",show_forecast:"Schneevorhersage anzeigen",forecast_default_open:"Schneevorhersage standardmäßig ausgeklappt",show_trend:"Trend-Indikatoren anzeigen (24h)",show_last_updated:"Zuletzt aktualisiert anzeigen",show_link:"Link-Symbol anzeigen",hide_closed_resorts:"Geschlossene Skigebiete ausblenden",hide_closed_resorts_helper:"Blendet nur Skigebiete aus, die zwischen Winter- und Sommersaison liegen. Gebiete im Sommerbetrieb bleiben sichtbar, auch wenn nicht Ski gefahren werden kann.",sort_by:"Sortieren nach",sort_by_options:{mountain:"Schnee (Berg)",valley:"Schnee (Tal)",new:"Neuschnee",lift:"Offene Lifte",classical:"Klassische Loipen",skating:"Skating-Loipen",update:"Letzte Aktualisierung"},show_trails:"Loipenstatistiken anzeigen"},card:{resort_not_found:"Skigebiet nicht gefunden: {resort}",lifts_open:"Lifte",header:{snow_mountain:"Berg",snow_valley:"Tal",new_snow:"Neu",snow_condition:"Schneezustand",slope_condition:"Pistenzustand",avalanche_warning:"Lawinenwarnstufe",last_snowfall:"Letzter Schneefall",slopes_info:"Pisten",slopes_info_km:"Pisten (km)",slopes_open_km:"Offen",slopes_total:"Gesamt",classical_trails:"Klassische Loipen",skating_trails:"Skating-Loipen",classical_condition:"Klassischer Zustand",skating_condition:"Skating-Zustand",operation_status:"Betriebsstatus",link_title:"{resortName} Detailseite auf bergfex öffnen"},forecast:{daily:"Täglich",summary:"Zusammenfassung",hour:"{hours} Stunden",today:"Heute",tomorrow:"Morgen"},accordion:{conditions:"Bedingungen",forecast:"Schneevorhersage"},status:{open:"Offen",closed:"Geschlossen",unknown:"Unbekannt",winter_season:"Wintersaison",summer_season:"Sommersaison",season_from:"ab {date}",season_last_year:"letztes Jahr: {date}"},warnings:{not_found:"Skigebiet nicht gefunden: {subject}",unavailable:"Für {subject} werden keine Daten gemeldet.",wrong_domain:"{subject} ist eine {actual}-Entität, benötigt wird eine {expected}.",not_numeric:"{subject} meldet keine Zahl (der Wert ist „{state}“)."}},common:{errors:{no_resorts:"Sie müssen mindestens ein Skigebiet definieren."}}},en:{editor:{groups:{core:"Core Configuration",display:"Display",ski_only:"Ski Resort Options",cross_country_only:"Cross-country options"},title:"Title (Optional)",resorts:"Resort Entities",show_snow:"Show snow information",show_lifts_slopes:"Show lift & slope statistics",show_conditions:"Show conditions section",conditions_default_open:"Conditions section expanded by default",show_forecast:"Show snow forecast",forecast_default_open:"Snow forecast expanded by default",show_trend:"Show trend indicators (24h)",show_last_updated:"Show last updated",show_link:"Show link icon",hide_closed_resorts:"Hide closed resorts",hide_closed_resorts_helper:"Only hides resorts between the winter and summer seasons. Resorts in summer operation stay visible, even though you cannot ski there.",sort_by:"Sort by",sort_by_options:{mountain:"Snow (Mountain)",valley:"Snow (Valley)",new:"New Snow",lift:"Lifts Open",classical:"Classical Trails",skating:"Skating Trails",update:"Last Update"},show_trails:"Show trail statistics"},card:{resort_not_found:"Resort not found: {resort}",lifts_open:"Lifts",header:{snow_mountain:"Mountain",snow_valley:"Valley",new_snow:"New",snow_condition:"Snow Condition",slope_condition:"Slope Condition",avalanche_warning:"Avalanche Warning",last_snowfall:"Last Snowfall",slopes_info:"Slopes",slopes_info_km:"Slopes (km)",slopes_open_km:"Open",slopes_total:"Total",classical_trails:"Classical Trails",skating_trails:"Skating Trails",classical_condition:"Classical Condition",skating_condition:"Skating Condition",operation_status:"Operation Status",link_title:"Open {resortName} detail page on bergfex"},forecast:{daily:"Daily",summary:"Summary",hour:"{hours} Hours",today:"Today",tomorrow:"Tomorrow"},accordion:{conditions:"Conditions",forecast:"Snow Forecast"},status:{open:"Open",closed:"Closed",unknown:"Unknown",winter_season:"Winter season",summer_season:"Summer season",season_from:"from {date}",season_last_year:"last year: {date}"},warnings:{not_found:"Resort not found: {subject}",unavailable:"No data is being reported for {subject}.",wrong_domain:"{subject} is a {actual} entity, but a {expected} is needed.",not_numeric:'{subject} does not report a number (it reads "{state}").'}},common:{errors:{no_resorts:"You need to define at least one resort entity."}}},fr:{editor:{groups:{core:"Configuration",display:"Affichage",ski_only:"Options station de ski",cross_country_only:"Options pour le ski de fond"},title:"Titre (optionnel)",resorts:"Stations de ski",show_snow:"Afficher les info sur la neige",show_lifts_slopes:"Afficher statistiques remontées & pistes",show_conditions:"Afficher la section des conditions",conditions_default_open:"Section conditions développée par défaut",show_forecast:"Afficher les prévisions de neige",forecast_default_open:"Prévisions de neige développées par défaut",show_trend:"Afficher les tendances (24 h)",show_last_updated:"Afficher la dernière mise à jour",show_link:"Afficher le lien",hide_closed_resorts:"Masquer les stations fermées",hide_closed_resorts_helper:"Masque uniquement les stations situées entre la saison d'hiver et celle d'été. Les stations en exploitation estivale restent visibles, même si le ski y est impossible.",sort_by:"Trier par",sort_by_options:{mountain:"Neige (au sommet)",valley:"Neige (dans la vallée)",new:"Dernière chute de neige",lift:"Remontées ouvertes",classical:"Pistes classiques",skating:"Back-country",update:"Dernière mise à jour"},show_trails:"Afficher les statistiques de pistes"},card:{resort_not_found:"Station non trouvée : {resort}",lifts_open:"Remontées ouvertes",header:{snow_mountain:"Sommet",snow_valley:"Vallée",new_snow:"Dernière chute de neige",snow_condition:"État de la neige",slope_condition:"État des pistes",avalanche_warning:"Risque avalanche",last_snowfall:"Dernière chute de neige",slopes_info:"Pistes",slopes_info_km:"Pistes (km)",slopes_open_km:"Ouvertes",slopes_total:"Total",classical_trails:"Pistes classiques",skating_trails:"Pistes de skating",classical_condition:"État classique",skating_condition:"État backcountry",operation_status:"Statut",link_title:"Ouvrir la page bergfex de {resortName}"},forecast:{daily:"Quotidien",summary:"Résumé",hour:"{hours} heure(s)",today:"Aujourd’hui",tomorrow:"Demain"},accordion:{conditions:"Conditions",forecast:"Prévisions de neige"},status:{open:"Ouvert",closed:"Fermé",unknown:"Inconnu",winter_season:"Saison hivernale",summer_season:"Saison estivale",season_from:"à partir du {date}",season_last_year:"l'an dernier : {date}"},warnings:{not_found:"Station introuvable : {subject}",unavailable:"Aucune donnée n’est remontée pour {subject}.",wrong_domain:"{subject} est une entité {actual}, mais une entité {expected} est attendue.",not_numeric:"{subject} ne renvoie pas de nombre (la valeur est « {state} »)."}},common:{errors:{no_resorts:"Vous devez définir au moins une station de ski."}}},pl:{editor:{groups:{core:"Główna konfiguracja",display:"Wyświetlacz",ski_only:"Opcje kurortu narciarskiego",cross_country_only:"Opcje tras biegowych"},title:"Tytuł (opcjonalnie)",resorts:"Wpisy kurortu",show_snow:"Pokaż informację o śniegu",show_lifts_slopes:"Pokaż statystyki wyciągów i stoków",show_conditions:"Pokaż sekcję warunków",conditions_default_open:"Sekcja warunków domyślnie rozwinięta",show_forecast:"Pokaż prognozę śniegu",forecast_default_open:"Prognoza śniegu domyślnie rozwinięta",show_trend:"Pokaż indykator trendu (24g)",show_last_updated:"Pokaż ostatnio aktualizowane",show_link:"Pokaż ikonę linku",hide_closed_resorts:"Ukryj zamknięte kurorty",hide_closed_resorts_helper:"Ukrywa tylko ośrodki znajdujące się między sezonem zimowym a letnim. Ośrodki w ruchu letnim pozostają widoczne, nawet jeśli nie można w nich jeździć na nartach.",sort_by:"Posortuj",sort_by_options:{mountain:"Śnieg (szczyt)",valley:"Śnieg (dolina)",new:"Nowy śnieg",lift:"Otwarte wyciągi",classical:"Trasy klasyczne",skating:"Trasy łyżwiarskie",update:"Ostatnio aktualizowane"},show_trails:"Pokaż statystyki tras"},card:{resort_not_found:"Nie znaleziono resortu: {resort}",lifts_open:"Wyciągi",header:{snow_mountain:"Szczyt",snow_valley:"Dolina",new_snow:"Nowy opad",snow_condition:"Warunki śniegowe",slope_condition:"Warunki na stoku",avalanche_warning:"Ostrzeżenie lawinowe",last_snowfall:"Ostatni opad",slopes_info:"Trasy",slopes_info_km:"Trasy (km)",slopes_open_km:"Otwarte",slopes_total:"Całkowite",classical_trails:"Trasy klasyczne",skating_trails:"Trasy łyżwiarskie",classical_condition:"Stan tras klasycznych",skating_condition:"Stan tras łyżwiarskich",operation_status:"Status działania",link_title:"Otwórz informację o  {resortName} na stronie Bergfex"},forecast:{daily:"Dzienna",summary:"Podsumowanie",hour:"{hours} godziny",today:"Dziś",tomorrow:"Jutro"},accordion:{conditions:"Warunki",forecast:"Prognoza opadów"},status:{open:"Otwarte",closed:"Zamknięte",unknown:"Nieznany",winter_season:"Sezon zimowy",summer_season:"Sezon letni",season_from:"od {date}",season_last_year:"w zeszłym roku: {date}"},warnings:{not_found:"Nie znaleziono ośrodka: {subject}",unavailable:"Dla {subject} nie są raportowane żadne dane.",wrong_domain:"{subject} to encja {actual}, a wymagana jest {expected}.",not_numeric:"{subject} nie zwraca liczby (wartość to „{state}”)."}},common:{errors:{no_resorts:"Musisz zdefiniować przynajmniej jeden wpis o resorcie."}}}};function St(t,e){let s=xt[t];for(const t of e){if("object"!=typeof s||null===s)return;s=s[t]}return"string"==typeof s?s:void 0}function At(t,e,s={}){const i=t?.language||"en",o=e.replace("component.bergfex-card.","").split("."),n=St(i,o)??St("en",o);if("string"==typeof n){let t=n;for(const e in s)t=t.replace(`{${e}}`,String(s[e]));return t}return e}const Nt=(t,e,s,i)=>{const o=new CustomEvent(e,{bubbles:!0,cancelable:!1,composed:!0,...i,detail:s});t.dispatchEvent(o)};function Ct(t){if(null==t||""===t)return null;const e=t instanceof Date?t:new Date(t);return Number.isNaN(e.getTime())?null:e}function Et(t,e){const s=Ct(t);if(!s)return"";const i=new Date,o=Math.round((i.getTime()-s.getTime())/1e3);try{const t=new Intl.RelativeTimeFormat(e.language,{numeric:"auto"});if(o<60)return t.format(-o,"second");const s=Math.round(o/60);if(s<60)return t.format(-s,"minute");const i=Math.round(s/60);if(i<24)return t.format(-i,"hour");const n=Math.round(i/24);return t.format(-n,"day")}catch{return function(t,e){const s=Ct(t);if(!s)return"";const i=new Date,o={hour:"numeric",minute:"2-digit"};return s.getDate()===i.getDate()&&s.getMonth()===i.getMonth()&&s.getFullYear()===i.getFullYear()||Object.assign(o,{year:"numeric",month:"short",day:"2-digit"}),"12"===e.locale?.time_format&&(o.hour12=!0),s.toLocaleString(e.language,o)}(t,e)}}const Pt=r`:host ::slotted(.card-content),.card-content{display:flex;flex-direction:column;gap:12px;padding:16px}.resort{border:1px solid var(--divider-color);border-radius:var(--ha-card-border-radius, 12px);cursor:pointer;display:flex;flex-direction:column;padding:12px;transition:background-color .2s ease-in-out}.resort:hover{background-color:rgba(var(--rgb-primary-text-color), 0.05)}.resort-header{align-items:center;display:flex;justify-content:space-between}.resort-name{font-size:1.2em;font-weight:500}.resort-status-group{align-items:flex-end;display:flex;flex-direction:column;gap:2px}.season-teaser{color:var(--secondary-text-color);font-size:.75em;white-space:nowrap}.resort-status{background-color:var(--divider-color);border-radius:4px;color:var(--primary-text-color);font-size:.9em;font-weight:500;padding:2px 6px;text-transform:uppercase}.resort-status.open{background-color:var(--label-badge-green)}.resort-status.closed{background-color:var(--label-badge-red)}.resort-status.winter-season{background-color:var(--label-badge-green);opacity:.65}.resort-status.summer-season{background-color:var(--label-badge-yellow);color:rgba(0,0,0,.87)}.details{display:grid;gap:8px;grid-template-columns:repeat(3, minmax(0, 1fr));padding-top:12px}.details.cross-country-details{grid-template-columns:repeat(2, minmax(0, 1fr))}.detail-item{--mdc-icon-size: 24px;align-items:center;cursor:pointer;display:flex;gap:8px}.detail-item ha-icon{color:var(--secondary-text-color)}.detail-item svg,.custom-icon{align-items:center;display:flex;height:var(--mdc-icon-size, 24px);justify-content:center;width:var(--mdc-icon-size, 24px)}.detail-item svg svg,.custom-icon svg{height:100%;width:100%}.detail-item svg.stroke svg,.custom-icon.stroke svg{stroke:var(--secondary-text-color)}.detail-item svg.fill svg,.custom-icon.fill svg{fill:var(--secondary-text-color)}.detail-item-value{align-items:flex-start;display:flex;flex-direction:column;font-size:1.1em;width:calc(100% - 32px)}.detail-item-label{color:var(--secondary-text-color);font-size:.8em}.detail-item.n-a{opacity:.5}.value-row{align-items:center;display:flex;justify-content:space-between;width:100%}.trend-icon{--mdc-icon-size: 18px;display:inline-block;margin-left:4px;vertical-align:middle}.trend-icon.up{color:var(--label-badge-green, #4caf50)}.trend-icon.down{color:var(--label-badge-red, #f44336)}.trend-icon.same{color:var(--secondary-text-color);opacity:.5}.resort-footer{align-items:center;border-top:1px solid var(--divider-color);display:flex;justify-content:space-between;padding:12px 0 0}.link-icon{color:var(--secondary-text-color);display:flex;text-decoration:none}.last-updated{align-items:center;color:var(--secondary-text-color);cursor:pointer;display:flex;font-size:.8em;gap:4px;justify-content:flex-end}.warning{color:var(--error-color)}.progress-bar-container{background-color:var(--divider-color);border-radius:2px;height:4px;margin-top:4px;overflow:hidden;width:100%}.progress-bar-fill{background-color:var(--primary-color);border-radius:2px;height:100%;transition:width .3s ease-in-out}.accordion-container{border-top:1px solid var(--divider-color);margin-top:12px}.accordion-container+.accordion-container{margin-top:0}.accordion-header{align-items:center;color:var(--primary-text-color);cursor:pointer;display:flex;font-weight:500;justify-content:space-between;padding:12px 0}.accordion-header:hover{background-color:rgba(var(--rgb-primary-text-color), 0.02)}.accordion-content{padding-bottom:12px}.accordion-content.details{grid-template-columns:repeat(2, minmax(0, 1fr))}.forecast-tabs{border-bottom:1px solid var(--divider-color);display:flex;gap:16px;margin-bottom:12px}.forecast-tab{border-bottom:2px solid rgba(0,0,0,0);color:var(--secondary-text-color);cursor:pointer;font-weight:500;padding:8px 12px;transition:all .2s ease}.forecast-tab:hover{color:var(--primary-text-color)}.forecast-tab.active{border-bottom-color:var(--primary-color);color:var(--primary-color)}.forecast-carousel{align-items:center;display:flex;flex-direction:column;gap:8px;position:relative}.forecast-image-container{align-items:center;aspect-ratio:5/3;border-radius:8px;display:flex;justify-content:center;overflow:hidden;position:relative;width:100%}.forecast-image{height:100%;object-fit:contain;width:100%}.carousel-controls{align-items:center;display:flex;justify-content:space-between;margin-top:8px;width:100%}.carousel-btn{align-items:center;background:none;border:none;border-radius:50%;color:var(--primary-text-color);cursor:pointer;display:flex;justify-content:center;padding:8px;transition:background-color .2s}.carousel-btn:hover{background-color:rgba(var(--rgb-primary-text-color), 0.1)}.carousel-btn:disabled{color:var(--disabled-text-color);cursor:not-allowed}.carousel-label{font-size:1.1em;font-weight:500}`;var Tt='<svg height="5.485163mm" viewBox="0 0 5.8208332 5.4851627" width="5.820833mm"\n    xmlns="http://www.w3.org/2000/svg">\n    <g transform="matrix(1.4664468 0 0 1.4664092 -91.591331 -91.904945)">\n        <path\n            d="m65.27 62.689c.183-.037.29-.008.375.088.075.085.084.24.037.339-.053.113-.215.169-.339.157-.104-.01-.229-.082-.256-.183-.038-.142.025-.365.183-.401z" />\n        <path\n            d="m64.248 63.2s.552-.094.803 0c.242.091.585.511.585.511l.365-.365s.139-.043.182 0 0 .183 0 .183l-.365.365-.123.151-.133.032-.365-.292c-.213.103-.45.351-.505.612 0 0 .371.185.483.349.03.043.039.153.039.153l-.093.226-.129.412-.16.512-.256-.182.146-.439.146-.486-.62-.354-.366.438-.384.021-.748-.021v-.292l.895.009.42-.703.511-.584-.234-.034-.569.631s-.097-.012-.124-.047c-.038-.049-.023-.185-.023-.185l.475-.548z" />\n        <path d="m66.06 63.401.129.053-.882 2.595h-.22v-.11z" />\n        <path\n            d="m62.486 63.941 1.199-.077c.042.001.059.003.041.147l-1.241.064c-.042-.003-.017.01.001-.134z" />\n        <path\n            d="m62.494 64.88.677.64s.167.22.332.333c.075.051.27-.023.27-.023.06.146-.023.309-.206.26 0 0-.092-.011-.123-.041-.318-.303-.986-.986-.986-.986z" />\n        <path d="m66.293 65.976c.128-.041.165.02.109.182l-.072.184-.183.072h-2.922l-.11-.219h2.959z" />\n    </g>\n</svg>',jt='<svg height="5.816813mm" viewBox="0 0 5.8207846 5.8168125" width="5.820785mm"\n    xmlns="http://www.w3.org/2000/svg">\n    <path\n        d="m146.23391 74.101876c-1.14758-.322091-2.11388-.608331-2.14733-.636091-.0334-.02776-.0608-.108614-.0608-.179677v-.129205l.0961-.06298.0961-.06298.25793.06981.25792.06982.56924-.595103.56924-.595102.27313-.597014c.15023-.328357.29373-.623828.31889-.656601.0252-.03277.21474-.194992.42129-.360486.20655-.165495.37555-.303341.37556-.306325.00001-.003-.091.000688-.20221.0082l-.20224.01358-.33813.251109c-.18597.13811-.36251.285922-.39232.328472-.0298.04255-.10067.08247-.1575.0887-.0568.0062-.14399-.0072-.19371-.02985-.0497-.02265-.10401-.081-.12064-.129668-.0179-.05241-.35705-.333699-.83186-.689982l-.80161-.601501.012-.08403c.007-.04622.0433-.08999.0815-.09727.0428-.0082.35783.203155.82082.550577.41325.310099.77461.572734.80301.583633.0284.0109.26239-.137376.51998-.329498l.46835-.349314h.75066.75066l.10905.05639c.06.03101.15375.109522.20839.17446.0546.06494.11078.17897.12474.253405.0167.08913.003.19368-.0399.306229l-.0653.170892-.4208.334698c-.23143.184083-.42079.347695-.42079.36358 0 .01589.0834.121276.18544.234202.102.112924.21466.248173.25036.300551l.0649.09523v.588443.588443h.70737.70737l.10149.07983c.0598.04707.10148.118197.10148.173327 0 .05142-.0347.128162-.077.170531l-.077.07703h-1.14378-1.14378l-.59912-.156269c-.32951-.08595-.66539-.173625-.7464-.194837l-.14728-.03857.0461-.05552.0461-.05552h.8662.8662l-.0221-.12518c-.0122-.06885-.0424-.281174-.0673-.471834-.0249-.190659-.0645-.36743-.0881-.392826-.0236-.02539-.17114-.116473-.32784-.202393l-.2849-.156218-.52395.533504c-.28817.293428-.65979.658876-.82581.812106-.16602.153231-.29601.283727-.28888.28999.007.0063.74095.212729 1.6307.45881l1.61771.44742.0674.08163c.0371.04489.0674.11437.0674.154392 0 .04002-.0347.107432-.077.149801-.043.04303-.12379.0752-.18296.07288-.0583-.0023-1.04485-.267685-2.19243-.589775zm2.8867-4.068706c-.0683-.01447-.16944-.05594-.2247-.09215-.0553-.03621-.13332-.138153-.17345-.226536-.0401-.08838-.0733-.202887-.0738-.254455-.00052-.05157.0341-.164231.0768-.25036.0427-.08613.1238-.190098.18027-.231041.0587-.04252.18642-.0807.29795-.08903l.19527-.01459.13481.07378c.0741.04058.17352.141311.22084.223843.0473.08253.0863.210993.0867.285469.00027.07448-.0315.195246-.0707.268379-.0392.07313-.11422.16501-.16667.20417-.0525.03916-.15469.08417-.2272.100019-.0725.01585-.18772.01698-.25604.0025z"\n        stroke-width=".052895" transform="translate(-144.02094 -68.875018)" />\n</svg>';const zt="bergfex-card",Ot=`${zt}-editor`;class Mt extends ct{constructor(){super(...arguments),this._forecastState={},this._accordionState={},this._historyState={}}setConfig(t){if(!t||!t.resorts||!Array.isArray(t.resorts))throw new Error(At(this.hass,"common.errors.no_resorts"));this._config={..._t,...t},this._config.show_trend&&this._fetchHistory()}static async getConfigElement(){const t=await window.loadCardHelpers(),e=await t.createCardElement({type:"entities",entities:[]}),s=e?.constructor;return s?.getConfigElement&&await s.getConfigElement(),await Promise.resolve().then(function(){return It}),document.createElement(Ot)}static getStubConfig(t,e){const s=Mt._firstResortDevice(t,e);return{resorts:s?[s]:[]}}static _firstResortDevice(t,e){if(!t?.entities)return;const s=e?.length?e:Object.keys(t.entities);for(const e of s){const s=t.entities[e];if("bergfex"===s?.platform&&s.device_id)return s.device_id}}getCardSize(){const t=this._config?.resorts?.length??0;if(0===t)return 1;let e=2;return this._config.show_snow&&(e+=1),this._config.show_lifts_slopes&&(e+=1),this._config.show_trails&&(e+=1),this._config.show_conditions&&(e+=this._config.conditions_default_open?2:1),this._config.show_forecast&&(e+=this._config.forecast_default_open?3:1),1+t*e}getGridOptions(){return{columns:12,min_columns:6,rows:this.getCardSize(),min_rows:2}}_getResorts(t,e){const s={},i=Object.values(t.states);return e.resorts.forEach(e=>{if(!e)return;const o="string"==typeof e?e:e.device,n="object"==typeof e?e.name:void 0,a=function(t,e){const s=e??"";if(!t||!e||!t.devices?.[e])return{ok:!1,problem:{reason:"not_found",subject:s}};const i=Object.values(t.states).filter(s=>t.entities[s.entity_id]?.device_id===e&&(s.entity_id.startsWith("sensor.")||s.entity_id.startsWith("image.")));return 0===i.length?{ok:!1,problem:{reason:"unavailable",subject:s}}:{ok:!0,value:{deviceId:e,entities:i}}}(t,o);if(!a.ok)return void(s[o]={problem:a.problem,name:n});const r=a.value.entities;if(s[o]||(s[o]={forecast_days:[],forecast_summaries:[]}),n&&(s[o].name=n),r.forEach(t=>{const e=t.entity_id;if(e.endsWith("_operation_status"))s[o].operation_status=e;else if(e.endsWith("_status")){s[o].status=e;const i=t.attributes?.link,n=t.attributes?.icon;(i&&i.includes("/langlaufen/")||"mdi:ski-cross-country"===n||"mdi:ski-cross-country-skating"===n)&&(s[o].is_cross_country=!0)}e.endsWith("_snow_valley")&&(s[o].snow_valley=e),e.endsWith("_snow_mountain")&&(s[o].snow_mountain=e),e.endsWith("_new_snow")&&(s[o].new_snow=e),e.endsWith("_lifts_open_count")?s[o].lifts_open_count=e:e.endsWith("_lifts_open")&&!s[o].lifts_open_count&&(s[o].lifts_open=e),e.endsWith("_last_update")&&(s[o].last_update=e),e.endsWith("_snow_condition")&&(s[o].snow_condition=e),e.endsWith("_last_snowfall")&&(s[o].last_snowfall=e),e.endsWith("_avalanche_warning")&&(s[o].avalanche_warning=e),e.endsWith("_slopes_open_km")&&(s[o].slopes_open_km=e),e.endsWith("_slopes_open_count")?s[o].slopes_open_count=e:e.endsWith("_slopes_open")&&!s[o].slopes_open_count&&(s[o].slopes_open=e),e.endsWith("_slope_condition")&&(s[o].slope_condition=e),e.endsWith("_classical_open_km")&&(s[o].classical_trails_open=e),e.endsWith("_skating_open_km")&&(s[o].skating_trails_open=e),e.endsWith("_classical_condition")&&(s[o].classical_condition=e),e.endsWith("_skating_condition")&&(s[o].skating_condition=e),e.includes("_forecast_image_day_")&&s[o].forecast_days?.push(e),e.includes("_summary_image_")&&s[o].forecast_summaries?.push(e)}),s[o].forecast_days?.sort(),s[o].forecast_summaries?.sort((t,e)=>{const s=t=>{const e=t.match(/summary_(\d+)h/);return e?parseInt(e[1],10):0};return s(t)-s(e)}),!(s[o].forecast_days&&0!==s[o].forecast_days.length||s[o].forecast_summaries&&0!==s[o].forecast_summaries.length)){const t=s[o].status;if(t){const e=t.match(/^sensor\.(.+)_status$/);if(e){const t=`image.${e[1]}_snow_forecast`;i.forEach(e=>{e.entity_id.startsWith(t)&&(e.entity_id.includes("_day_")?s[o].forecast_days?.push(e.entity_id):e.entity_id.includes("_summary_")&&s[o].forecast_summaries?.push(e.entity_id))}),s[o].forecast_days?.sort(),s[o].forecast_summaries?.sort((t,e)=>{const s=t=>{const e=t.match(/summary_(\d+)h/);return e?parseInt(e[1],10):0};return s(t)-s(e)})}}}}),s}shouldUpdate(t){if(t.has("_config"))return!0;const e=t.get("hass");if(e){const s=t=>Object.values(this._getResorts(t,this._config)).flatMap(t=>Object.values(t)),i=new Set;for(const t of[...s(this.hass),...s(e)])"string"==typeof t&&i.add(t);const o=[...i].some(t=>e.states[t]!==this.hass.states[t]);return this.getOldConfig(t)?.show_trend!==this._config.show_trend&&this._config.show_trend&&this._fetchHistory(),o||e.language!==this.hass.language||t.has("_historyState")}return!0}getOldConfig(t){return t.get("_config")}async _fetchHistory(){if(!this.hass||!this._config.resorts)return;const t=this._getResorts(this.hass,this._config),e=Object.values(t).flatMap(t=>[t.snow_mountain,t.snow_valley,t.new_snow,t.lifts_open_count,t.lifts_open,t.slopes_open_km,t.slopes_open_count,t.slopes_open,t.classical_trails_open,t.skating_trails_open]).filter(Boolean);0!==e.length&&(this._historyState=await async function(t,e,s){if(0===e.length)return{};const i=new Date;i.setHours(i.getHours()-s);try{const s=await t.callWS({type:"history/history_during_period",start_time:i.toISOString(),end_time:i.toISOString(),entity_ids:e,no_attributes:!0}),o={};return Object.entries(s).forEach(([t,e])=>{Array.isArray(e)&&e.length>0&&(o[t]=e[0].s)}),o}catch(t){return console.error(`Error fetching history for ${e.join(", ")}:`,t),{}}}(this.hass,e,24))}_renderTrend(t,e){if(!this._config.show_trend)return W``;const s=this._historyState[t];if(void 0===s||this._isNA(e)||this._isNA(s))return W``;const i=parseFloat(e),o=parseFloat(s);return isNaN(i)||isNaN(o)?W``:i>o?W`<ha-icon class="trend-icon up" icon="mdi:trending-up"></ha-icon>`:i<o?W`<ha-icon class="trend-icon down" icon="mdi:trending-down"></ha-icon>`:W`<ha-icon class="trend-icon same" icon="mdi:trending-neutral"></ha-icon>`}_handleMoreInfo(t){Nt(this,"hass-more-info",{entityId:t})}_handleTabChange(t,e,s){s.stopPropagation(),this._forecastState={...this._forecastState,[t]:{...this._forecastState[t],tab:e,index:0}}}_handleCarouselChange(t,e,s,i){i.stopPropagation();const o=this._forecastState[t]||{tab:"daily",index:0};let n=o.index+("next"===e?1:-1);n<0&&(n=s-1),n>=s&&(n=0),this._forecastState={...this._forecastState,[t]:{...o,index:n}}}_toggleAccordion(t,e,s){s.stopPropagation();const i=this._accordionState[t]||{},o=i[e]??this._config[`${e}_default_open`]??!1;this._accordionState={...this._accordionState,[t]:{...i,[e]:!o}}}_formatForecastDate(t){const e=new Date;if(e.setDate(e.getDate()+t),0===t)return At(this.hass,"component.bergfex-card.card.forecast.today");if(1===t)return At(this.hass,"component.bergfex-card.card.forecast.tomorrow");{const t=this.hass.locale?.language||this.hass.language||"de";return`${e.toLocaleDateString(t,{weekday:"short"})}, ${e.getDate().toString().padStart(2,"0")}.${(e.getMonth()+1).toString().padStart(2,"0")}.`}}_renderProgressBar(t,e){const s=Math.min(100,Math.max(0,t/e*100));return W`
      <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width: ${s}%"></div>
      </div>
    `}_isNA(t){return["N/A","keine Meldung","unknown"].includes(t)}_statusBadge(t,e){if("open"===(t||"").toLowerCase())return{key:"open",variant:"open"};const s=(new Date).toISOString().slice(0,10),i=t=>{const i=e[`${t}_season_start`],o=e[`${t}_season_end`];return Boolean(i&&o&&i<=s&&s<=o)};return i("winter")?{key:"winter_season",variant:"winter-season"}:i("summer")?{key:"summer_season",variant:"summer-season"}:"closed"===(t||"").toLowerCase()?{key:"closed",variant:"closed"}:{key:"unknown",variant:""}}_winterTeaser(t){const e=t.winter_season_start;if(!e)return;const s=(new Date).toISOString().slice(0,10),i=t.winter_season_end;if(e<=s&&(!i||s<=i))return;const o=new Date(`${e}T00:00:00`);if(Number.isNaN(o.getTime()))return;const n=new Intl.DateTimeFormat(this.hass.language,{day:"2-digit",month:"2-digit"}).format(o);if(e>s)return At(this.hass,"component.bergfex-card.card.status.season_from",{date:n});return(Date.now()-o.getTime())/2630016e3>18?void 0:At(this.hass,"component.bergfex-card.card.status.season_last_year",{date:n})}_isOutOfSeason(t){const e=t.status?this.hass.states[t.status]:void 0;return!e||"open"!==e.state.toLowerCase()&&"closed"===this._statusBadge(e.state,e.attributes??{}).variant}_conditionText(t){return this._isNA(t)?At(this.hass,"component.bergfex-card.card.status.unknown"):t}_isCrossCountryResort(t){return!!(t.is_cross_country||t.classical_trails_open||t.skating_trails_open||t.classical_condition||t.skating_condition)}render(){if(!this._config)return W``;if(!this.hass||0===this._config.resorts.length)return W`
        <ha-card .header=${this._config.title} tabindex="0">
          <div class="card-content">
            <div class="warning">${At(this.hass,"common.errors.no_resorts")}</div>
          </div>
        </ha-card>
      `;let t=Object.entries(this._getResorts(this.hass,this._config));this._config.hide_closed_resorts&&(t=t.filter(([,t])=>!this._isOutOfSeason(t)));const e=this._config.sort_by;return e&&"none"!==e&&t.sort(([,t],[,s])=>{let i,o;switch(e){case"mountain":if(this._isCrossCountryResort(t)||this._isCrossCountryResort(s))break;i=t.snow_mountain?parseFloat(this.hass.states[t.snow_mountain].state):NaN,o=s.snow_mountain?parseFloat(this.hass.states[s.snow_mountain].state):NaN;break;case"valley":if(this._isCrossCountryResort(t)||this._isCrossCountryResort(s))break;i=t.snow_valley?parseFloat(this.hass.states[t.snow_valley].state):NaN,o=s.snow_valley?parseFloat(this.hass.states[s.snow_valley].state):NaN;break;case"new":if(this._isCrossCountryResort(t)||this._isCrossCountryResort(s))break;i=t.new_snow?parseFloat(this.hass.states[t.new_snow].state):NaN,o=s.new_snow?parseFloat(this.hass.states[s.new_snow].state):NaN;break;case"lift":{if(this._isCrossCountryResort(t)||this._isCrossCountryResort(s))break;const e=t=>{const e=t.lifts_open_count??t.lifts_open;return e?parseFloat(this.hass.states[e]?.state??""):NaN};i=e(t),o=e(s);break}case"classical":i=t.classical_trails_open?parseFloat(this.hass.states[t.classical_trails_open].state):NaN,o=s.classical_trails_open?parseFloat(this.hass.states[s.classical_trails_open].state):NaN;break;case"skating":i=t.skating_trails_open?parseFloat(this.hass.states[t.skating_trails_open].state):NaN,o=s.skating_trails_open?parseFloat(this.hass.states[s.skating_trails_open].state):NaN;break;case"update":{const e=Ct(t.last_update?this.hass.states[t.last_update]?.state:void 0)?.getTime(),i=Ct(s.last_update?this.hass.states[s.last_update]?.state:void 0)?.getTime();return void 0===e&&void 0===i?0:void 0===e?1:void 0===i?-1:i-e}}if("number"==typeof i&&"number"==typeof o){const t=isNaN(i),e=isNaN(o);return t&&e?0:t?1:e?-1:o-i}return 0}),W`
      <ha-card .header=${this._config.title} tabindex="0">
        <div class="card-content">
          ${t.map(([t,e])=>{const s=e.status;if(e.problem||!s){const s=e.problem??{reason:"unavailable",subject:e.name??t};return W` <div class="warning">${function(t,e){const s={subject:e.subject};return"wrong_domain"===e.reason&&(s.expected=e.expected,s.actual=e.actual),"not_numeric"===e.reason&&(s.state=e.state),At(t,`component.bergfex-card.card.warnings.${e.reason}`,s)}(this.hass,s)}</div> `}const i=this.hass.devices[t],o=e.name||i?.name_by_user||i?.name||"Unknown Resort",n=e.operation_status?this.hass.states[e.operation_status]:void 0,a=e.status?this.hass.states[e.status]:void 0,r=a?.state??"unknown",c=r,l=this._statusBadge(r,a?.attributes??{}),d=this._winterTeaser(a?.attributes??{}),h=At(this.hass,`component.bergfex-card.card.status.${l.key}`)||c,p=a?.attributes.link,u=e.snow_valley?this.hass.states[e.snow_valley]:void 0,_=e.snow_mountain?this.hass.states[e.snow_mountain]:void 0,f=e.new_snow?this.hass.states[e.new_snow]:void 0,m=e.lifts_open_count?this.hass.states[e.lifts_open_count]:void 0,g=m||(e.lifts_open?this.hass.states[e.lifts_open]:void 0),v=e.last_update?this.hass.states[e.last_update]:void 0,y=Ct(v?.state),w=e.snow_condition?this.hass.states[e.snow_condition]:void 0,b=e.slope_condition?this.hass.states[e.slope_condition]:void 0,$=e.last_snowfall?this.hass.states[e.last_snowfall]:void 0,k=e.avalanche_warning?this.hass.states[e.avalanche_warning]:void 0,x=e.slopes_open_km?this.hass.states[e.slopes_open_km]:void 0,S=e.slopes_open_count?this.hass.states[e.slopes_open_count]:void 0,A=S||(e.slopes_open?this.hass.states[e.slopes_open]:void 0),N=e.classical_trails_open?this.hass.states[e.classical_trails_open]:void 0,C=e.skating_trails_open?this.hass.states[e.skating_trails_open]:void 0,E=e.classical_condition?this.hass.states[e.classical_condition]:void 0,P=e.skating_condition?this.hass.states[e.skating_condition]:void 0,T=this._isCrossCountryResort(e),j=N?.attributes?.total,z=C?.attributes?.total,O=g?.attributes?.total,M=x?.attributes?.total,R=A?.attributes?.total,D=this._accordionState[t]?.conditions??this._config.conditions_default_open,L=this._accordionState[t]?.forecast??this._config.forecast_default_open;return W`
              <div class="resort" tabindex="0" @click=${()=>this._handleMoreInfo(s)}>
                <div class="resort-header">
                  <span class="resort-name">${o}</span>
                  <div class="resort-status-group">
                    <span
                      class=${wt({"resort-status":!0,[l.variant]:Boolean(l.variant)})}
                      >${h}</span
                    >
                    ${d?W`<span class="season-teaser">${d}</span>`:""}
                  </div>
                </div>

                <div class=${T?"details cross-country-details":"details"}>
                  ${this._config.show_snow&&!T?W`
                          <div
                            class=${wt({"detail-item":!0,"n-a":!_||isNaN(parseFloat(_.state))})}
                            @click=${t=>{t.stopPropagation(),_&&this._handleMoreInfo(_.entity_id)}}
                          >
                            <span class="custom-icon stroke">${kt('<?xml version="1.0" encoding="utf-8"?>\n\x3c!-- License: MIT. Made by Lucide Contributors: https://lucide.dev/ --\x3e\n<svg \n  xmlns="http://www.w3.org/2000/svg"\n  width="24"\n  height="24"\n  viewBox="0 0 24 24"\n  fill="none"\n  stroke="#000000"\n  stroke-width="2"\n  stroke-linecap="round"\n  stroke-linejoin="round"\n>\n  \x3c!-- Mountain --\x3e\n  <path d="M8 3l4 8 5-5 5 15H2L8 3z" />\n  <path d="M4.14 15.08c2.62-1.57 5.24-1.43 7.86.42 2.74 1.94 5.49 2 8.23.19" />\n\n  \x3c!-- Left-pointing arrow further right from first peak --\x3e\n  <g stroke-width="1">\n    <line x1="15" y1="3" x2="10" y2="3" />\n    <polyline points="12,1 10,3 12,5" />\n  </g>\n</svg>')}</span>
                            <div class="detail-item-value">
                              ${_&&!isNaN(parseFloat(_.state))?W`<div class="value-row">
                                      <span
                                        >${_.state}
                                        ${_.attributes.unit_of_measurement??""}</span
                                      >
                                      ${this._renderTrend(_.entity_id,_.state)}
                                    </div>`:W`<span>N/A</span>`}
                              <span class="detail-item-label"
                                >${At(this.hass,"component.bergfex-card.card.header.snow_mountain")}
                                ${_?.attributes.elevation?`(${_.attributes.elevation}m)`:""}</span
                              >
                            </div>
                          </div>
                          <div
                            class=${wt({"detail-item":!0,"n-a":!u||isNaN(parseFloat(u.state))})}
                            @click=${t=>{t.stopPropagation(),u&&this._handleMoreInfo(u.entity_id);const e=t.currentTarget;e.classList.add("clicked"),setTimeout(()=>{e.classList.remove("clicked")},500)}}
                          >
                            <span class="custom-icon stroke">${kt('<?xml version="1.0" encoding="utf-8"?>\n\x3c!-- License: MIT. Made by Lucide Contributors: https://lucide.dev/ --\x3e\n<svg \n  xmlns="http://www.w3.org/2000/svg"\n  width="24"\n  height="24"\n  viewBox="0 0 24 24"\n  fill="none"\n  stroke="#000000"\n  stroke-width="2"\n  stroke-linecap="round"\n  stroke-linejoin="round"\n>\n  <path d="M8 3l4 8 5-5 5 15H2L8 3z" />\n  <path d="M4.14 15.08c2.62-1.57 5.24-1.43 7.86.42 2.74 1.94 5.49 2 8.23.19" />\n\n  <g stroke-width="1">\n    <line x1="5" y1="17.5" x2="10" y2="17.5" />\n    <polyline points="8,15.5 5,17.5 8,19.5" />\n  </g>\n</svg>')}</span>
                            <div class="detail-item-value">
                              ${u&&!isNaN(parseFloat(u.state))?W`<div class="value-row">
                                      <span
                                        >${u.state} ${u.attributes.unit_of_measurement??""}</span
                                      >
                                      ${this._renderTrend(u.entity_id,u.state)}
                                    </div>`:W`<span>N/A</span>`}
                              <span class="detail-item-label"
                                >${At(this.hass,"component.bergfex-card.card.header.snow_valley")}
                                ${u?.attributes.elevation?`(${u.attributes.elevation}m)`:""}</span
                              >
                            </div>
                          </div>
                          <div
                            class=${wt({"detail-item":!0,"n-a":!f||isNaN(parseFloat(f.state))})}
                            @click=${t=>{t.stopPropagation(),f&&this._handleMoreInfo(f.entity_id)}}
                          >
                            <ha-icon icon="mdi:weather-snowy-heavy"></ha-icon>
                            <div class="detail-item-value">
                              ${f&&!isNaN(parseFloat(f.state))?W`<div class="value-row">
                                      <span>${f.state} ${f.attributes.unit_of_measurement??""}</span>
                                      ${this._renderTrend(f.entity_id,f.state)}
                                    </div>`:W`<span>N/A</span>`}
                              <span class="detail-item-label"
                                >${At(this.hass,"component.bergfex-card.card.header.new_snow")}</span
                              >
                            </div>
                          </div>
                        `:""}
                  ${T&&this._config.show_trails?W`
                          ${N?W`
                                  <div
                                    class=${wt({"detail-item":!0,"n-a":!N||isNaN(parseFloat(N.state))})}
                                    @click=${t=>{t.stopPropagation(),N&&this._handleMoreInfo(N.entity_id)}}
                                  >
                                    <span class="custom-icon fill">${kt(Tt)}</span>
                                    <div class="detail-item-value">
                                      ${N&&!isNaN(parseFloat(N.state))?(()=>{const t=parseFloat(N.state),e=N.attributes.unit_of_measurement??"km",s=j?parseFloat(String(j)):NaN;return isNaN(s)?W`<div class="value-row">
                                                <span>${N.state} ${e}</span>
                                                ${this._renderTrend(N.entity_id,N.state)}
                                              </div>`:W`<div class="value-row">
                                                    <span>${t}/${s} ${e}</span>
                                                    ${this._renderTrend(N.entity_id,N.state)}
                                                  </div>
                                                  ${this._renderProgressBar(t,s)}`})():W`<span>N/A</span>`}
                                      <span class="detail-item-label"
                                        >${At(this.hass,"component.bergfex-card.card.header.classical_trails")}</span
                                      >
                                    </div>
                                  </div>
                                `:""}
                          ${C?W`
                                  <div
                                    class=${wt({"detail-item":!0,"n-a":!C||isNaN(parseFloat(C.state))})}
                                    @click=${t=>{t.stopPropagation(),C&&this._handleMoreInfo(C.entity_id)}}
                                  >
                                    <span class="custom-icon fill">${kt(jt)}</span>
                                    <div class="detail-item-value">
                                      ${C&&!isNaN(parseFloat(C.state))?(()=>{const t=parseFloat(C.state),e=C.attributes.unit_of_measurement??"km",s=z?parseFloat(String(z)):NaN;return isNaN(s)?W`<div class="value-row">
                                                <span>${C.state} ${e}</span>
                                                ${this._renderTrend(C.entity_id,C.state)}
                                              </div>`:W`<div class="value-row">
                                                    <span>${t}/${s} ${e}</span>
                                                    ${this._renderTrend(C.entity_id,C.state)}
                                                  </div>
                                                  ${this._renderProgressBar(t,s)}`})():W`<span>N/A</span>`}
                                      <span class="detail-item-label"
                                        >${At(this.hass,"component.bergfex-card.card.header.skating_trails")}</span
                                      >
                                    </div>
                                  </div>
                                `:""}
                        `:W`
                          ${this._config.show_lifts_slopes&&g?W`
                                  <div
                                    class=${wt({"detail-item":!0,"n-a":!g||isNaN(parseFloat(g.state))})}
                                    @click=${t=>{t.stopPropagation(),g&&this._handleMoreInfo(g.entity_id)}}
                                  >
                                    <ha-icon icon="mdi:gondola"></ha-icon>
                                    <div class="detail-item-value">
                                      ${g&&!isNaN(parseFloat(g.state))?(()=>{const t=parseFloat(g.state),e=O?parseFloat(String(O)):NaN;return isNaN(e)?W`<div class="value-row">
                                                <span>${g.state}</span>
                                                ${this._renderTrend(g.entity_id,g.state)}
                                              </div>`:W`<div class="value-row">
                                                    <span>${t}/${e}</span>
                                                    ${this._renderTrend(g.entity_id,g.state)}
                                                  </div>
                                                  ${this._renderProgressBar(t,e)}`})():W`<span>N/A</span>`}
                                      <span class="detail-item-label"
                                        >${At(this.hass,"component.bergfex-card.card.lifts_open")}</span
                                      >
                                    </div>
                                  </div>
                                `:""}
                          ${this._config.show_lifts_slopes&&(x||A)?W`
                                  ${x?W`
                                          <div
                                            class=${wt({"detail-item":!0,"n-a":!x||isNaN(parseFloat(x.state))})}
                                            @click=${t=>{t.stopPropagation(),x&&this._handleMoreInfo(x.entity_id)}}
                                          >
                                            <span class="custom-icon stroke">
                                              <ha-icon icon="mdi:slope-downhill"></ha-icon>
                                            </span>
                                            <div class="detail-item-value">
                                              ${x&&!isNaN(parseFloat(x.state))?(()=>{const t=parseFloat(x.state),e=M?parseFloat(String(M)):NaN,s=x.attributes.unit_of_measurement??"km";return isNaN(e)?W`<div class="value-row">
                                                        <span>${x.state} ${s}</span>
                                                        ${this._renderTrend(x.entity_id,x.state)}
                                                      </div>`:W`<div class="value-row">
                                                            <span>${t}/${e} ${s}</span>
                                                            ${this._renderTrend(x.entity_id,x.state)}
                                                          </div>
                                                          ${this._renderProgressBar(t,e)}`})():W`<span>N/A</span>`}
                                              <span class="detail-item-label"
                                                >${At(this.hass,"component.bergfex-card.card.header.slopes_info_km")}</span
                                              >
                                            </div>
                                          </div>
                                        `:""}
                                  ${A&&R?W`
                                          <div
                                            class=${wt({"detail-item":!0,"n-a":!A||isNaN(parseFloat(A.state))||isNaN(parseFloat(String(R??NaN)))})}
                                            @click=${t=>{t.stopPropagation(),A&&this._handleMoreInfo(A.entity_id)}}
                                          >
                                            <ha-icon icon="mdi:counter"></ha-icon>
                                            <div class="detail-item-value">
                                              ${A&&!isNaN(parseFloat(A.state))?(()=>{const t=parseFloat(A.state),e=R?parseFloat(String(R)):NaN;return isNaN(e)?W`<div class="value-row">
                                                        <span>${A.state}</span>
                                                        ${this._renderTrend(A.entity_id,A.state)}
                                                      </div>`:W`<div class="value-row">
                                                            <span>${t}/${e}</span>
                                                            ${this._renderTrend(A.entity_id,A.state)}
                                                          </div>
                                                          ${this._renderProgressBar(t,e)}`})():W`<span>N/A</span>`}
                                              <span class="detail-item-label"
                                                >${At(this.hass,"component.bergfex-card.card.header.slopes_info")}
                                                (${At(this.hass,"component.bergfex-card.card.header.slopes_total")})</span
                                              >
                                            </div>
                                          </div>
                                        `:A?W`
                                            <div
                                              class=${wt({"detail-item":!0,"n-a":!A||isNaN(parseFloat(A.state))})}
                                              @click=${t=>{t.stopPropagation(),A&&this._handleMoreInfo(A.entity_id)}}
                                            >
                                              <ha-icon icon="mdi:counter"></ha-icon>
                                              <div class="detail-item-value">
                                                ${A&&!isNaN(parseFloat(A.state))?W`<div class="value-row">
                                                        <span>${A.state}</span>
                                                        ${this._renderTrend(A.entity_id,A.state)}
                                                      </div>`:W`<span>N/A</span>`}
                                                <span class="detail-item-label"
                                                  >${At(this.hass,"component.bergfex-card.card.header.slopes_info")}</span
                                                >
                                              </div>
                                            </div>
                                          `:""}
                                `:""}
                        `}
                </div>

                ${this._config.show_conditions&&(w||b||k||$||n||E||P)?W`
                        <div class="accordion-container">
                          <div
                            class="accordion-header"
                            @click=${e=>this._toggleAccordion(t,"conditions",e)}
                          >
                            <span>${At(this.hass,"component.bergfex-card.card.accordion.conditions")}</span>
                            <ha-icon icon=${D?"mdi:chevron-up":"mdi:chevron-down"}></ha-icon>
                          </div>
                          ${D?W`
                                  <div class="accordion-content details">
                                    ${this._config.show_conditions&&(w||b)&&!T?W`
                                            ${w?W`
                                                    <div
                                                      class=${wt({"detail-item":!0,"n-a":this._isNA(w.state)})}
                                                      @click=${t=>{t.stopPropagation(),w&&this._handleMoreInfo(w.entity_id)}}
                                                    >
                                                      <ha-icon icon="mdi:weather-snowy"></ha-icon>
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(w.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${At(this.hass,"component.bergfex-card.card.header.snow_condition")}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `:""}
                                            ${b?W`
                                                    <div
                                                      class=${wt({"detail-item":!0,"n-a":this._isNA(b.state)})}
                                                      @click=${t=>{t.stopPropagation(),b&&this._handleMoreInfo(b.entity_id)}}
                                                    >
                                                      <ha-icon icon="mdi:ski"></ha-icon>
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(b.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${At(this.hass,"component.bergfex-card.card.header.slope_condition")}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `:""}
                                          `:""}
                                    ${this._config.show_conditions&&k&&!T?W`
                                            <div
                                              class=${wt({"detail-item":!0,"n-a":this._isNA(k.state)})}
                                              @click=${t=>{t.stopPropagation(),k&&this._handleMoreInfo(k.entity_id)}}
                                            >
                                              <ha-icon icon="mdi:alert"></ha-icon>
                                              <div class="detail-item-value">
                                                <span>${this._conditionText(k.state)}</span>
                                                <span class="detail-item-label"
                                                  >${At(this.hass,"component.bergfex-card.card.header.avalanche_warning")}</span
                                                >
                                              </div>
                                            </div>
                                          `:""}
                                    ${this._config.show_conditions&&(E||P)?W`
                                            ${E?W`
                                                    <div
                                                      class=${wt({"detail-item":!0,"n-a":this._isNA(E.state)})}
                                                      @click=${t=>{t.stopPropagation(),E&&this._handleMoreInfo(E.entity_id)}}
                                                    >
                                                      <span class="custom-icon fill"
                                                        >${kt(Tt)}</span
                                                      >
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(E.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${At(this.hass,"component.bergfex-card.card.header.classical_condition")}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `:""}
                                            ${P?W`
                                                    <div
                                                      class=${wt({"detail-item":!0,"n-a":this._isNA(P.state)})}
                                                      @click=${t=>{t.stopPropagation(),P&&this._handleMoreInfo(P.entity_id)}}
                                                    >
                                                      <span class="custom-icon fill"
                                                        >${kt(jt)}</span
                                                      >
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(P.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${At(this.hass,"component.bergfex-card.card.header.skating_condition")}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `:""}
                                          `:""}
                                    ${$?W`
                                            <div
                                              class=${wt({"detail-item":!0,"n-a":this._isNA($.state)})}
                                              @click=${t=>{t.stopPropagation(),this._handleMoreInfo($.entity_id)}}
                                            >
                                              <ha-icon icon="mdi:calendar-clock"></ha-icon>
                                              <div class="detail-item-value">
                                                <span>${this._conditionText($.state)}</span>
                                                <span class="detail-item-label"
                                                  >${At(this.hass,"component.bergfex-card.card.header.last_snowfall")}</span
                                                >
                                              </div>
                                            </div>
                                          `:""}
                                    ${this._config.show_conditions&&n?W`
                                            <div
                                              class=${wt({"detail-item":!0,"n-a":this._isNA(n.state)})}
                                              @click=${t=>{t.stopPropagation(),n&&this._handleMoreInfo(n.entity_id)}}
                                            >
                                              <ha-icon icon="mdi:information-outline"></ha-icon>
                                              <div class="detail-item-value">
                                                <span>${this._conditionText(n.state)}</span>
                                                <span class="detail-item-label"
                                                  >${At(this.hass,"component.bergfex-card.card.header.operation_status")}</span
                                                >
                                              </div>
                                            </div>
                                          `:""}
                                  </div>
                                `:""}
                        </div>
                      `:""}
                ${(()=>{if(!this._config.show_forecast)return"";const s=e.forecast_days&&e.forecast_days.length>0&&e.forecast_days.some(t=>{const e=this.hass.states[t];return e&&e.attributes.entity_picture}),i=e.forecast_summaries&&e.forecast_summaries.length>0&&e.forecast_summaries.some(t=>{const e=this.hass.states[t];return e&&e.attributes.entity_picture});return s||i?W`
                    <div class="accordion-container">
                      <div
                        class="accordion-header"
                        @click=${e=>this._toggleAccordion(t,"forecast",e)}
                      >
                        <span>${At(this.hass,"component.bergfex-card.card.accordion.forecast")}</span>
                        <ha-icon icon=${L?"mdi:chevron-up":"mdi:chevron-down"}></ha-icon>
                      </div>
                      ${L?W`
                              <div class="forecast-container">
                                <div class="forecast-tabs">
                                  ${s?W`
                                          <div
                                            class="forecast-tab ${this._forecastState[t]&&"daily"!==this._forecastState[t].tab?"":"active"}"
                                            @click=${e=>this._handleTabChange(t,"daily",e)}
                                          >
                                            ${At(this.hass,"component.bergfex-card.card.forecast.daily")}
                                          </div>
                                        `:""}
                                  ${i?W`
                                          <div
                                            class="forecast-tab ${"summary"===this._forecastState[t]?.tab?"active":""}"
                                            @click=${e=>this._handleTabChange(t,"summary",e)}
                                          >
                                            ${At(this.hass,"component.bergfex-card.card.forecast.summary")}
                                          </div>
                                        `:""}
                                </div>

                                <div class="forecast-carousel">
                                  ${(()=>{const s=this._forecastState[t]?.tab||"daily",i="daily"===s?e.forecast_days:e.forecast_summaries,o=this._forecastState[t]?.index||0;if(!i||0===i.length)return W``;const n=i[o],a=this.hass.states[n],r=a?.attributes.entity_picture;let c;if("daily"===s){const t=n.match(/day_(\d+)/),e=t?parseInt(t[1],10):o;c=this._formatForecastDate(e)}else{const t=n.match(/summary_image_(\d+)h/),e=t?t[1]:"";c=At(this.hass,"component.bergfex-card.card.forecast.hour",{hours:e})}return W`
                                      <div class="forecast-image-container">
                                        ${r?W`<img
                                                src="${r}"
                                                class="forecast-image"
                                                alt="${c}"
                                                @click=${t=>{t.stopPropagation(),this._handleMoreInfo(n)}}
                                                style="cursor: pointer;"
                                              />`:W`<span>Image not available</span>`}
                                      </div>
                                      <div class="carousel-controls">
                                        <button
                                          class="carousel-btn"
                                          @click=${e=>this._handleCarouselChange(t,"prev",i.length,e)}
                                          ?disabled=${i.length<=1}
                                        >
                                          <ha-icon icon="mdi:chevron-left"></ha-icon>
                                        </button>
                                        <span class="carousel-label">${c}</span>
                                        <button
                                          class="carousel-btn"
                                          @click=${e=>this._handleCarouselChange(t,"next",i.length,e)}
                                          ?disabled=${i.length<=1}
                                        >
                                          <ha-icon icon="mdi:chevron-right"></ha-icon>
                                        </button>
                                      </div>
                                    `})()}
                                </div>
                              </div>
                            `:""}
                    </div>
                  `:""})()}

                <div class="resort-footer">
                  ${this._config.show_link&&p?W`
                          <a
                            href=${p}
                            target="_blank"
                            class="link-icon"
                            title=${At(this.hass,"component.bergfex-card.card.link_title",{resortName:o})}
                            @click=${t=>t.stopPropagation()}
                          >
                            <ha-icon icon="mdi:link-variant"></ha-icon>
                          </a>
                        `:W`<div></div>`}
                  ${this._config.show_last_updated&&v&&y?W`
                          <div
                            class="last-updated"
                            @click=${t=>{t.stopPropagation(),v&&this._handleMoreInfo(v.entity_id)}}
                          >
                            <ha-icon icon="mdi:clock-outline"></ha-icon>
                            <span>${Et(y,this.hass)}</span>
                          </div>
                        `:""}
                </div>
              </div>
            `})}
        </div>
      </ha-card>
    `}static{this.styles=r`
    ${a(Pt)}
  `}}t([pt({attribute:!1})],Mt.prototype,"hass",void 0),t([
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function(t){return(e,s,i)=>((t,e,s)=>(s.configurable=!0,s.enumerable=!0,Reflect.decorate&&"object"!=typeof e&&Object.defineProperty(t,e,s),s))(e,s,{get(){return(e=>e.renderRoot?.querySelector(t)??null)(this)}})}("ha-card")],Mt.prototype,"_card",void 0),t([ut()],Mt.prototype,"_config",void 0),t([ut()],Mt.prototype,"_forecastState",void 0),t([ut()],Mt.prototype,"_accordionState",void 0),t([ut()],Mt.prototype,"_historyState",void 0),customElements.get(zt)?console.warn(`${zt}: another copy of this card is already loaded, so this one stays inactive. The card now ships with the Bergfex integration - uninstall "Bergfex Card" from HACS and reload your browser.`):customElements.define(zt,Mt),"undefined"!=typeof window&&(window.customCards=window.customCards||[],window.customCards.some(t=>t.type===zt)||window.customCards.push({type:zt,name:"Bergfex Card",description:"A Lovelace card to display ski resort conditions from Bergfex.",documentationURL:"https://github.com/timmaurice/bergfex",getEntitySuggestion:(t,e)=>{const s=t.entities[e];return"bergfex"===s?.platform&&s.device_id?{config:{type:`custom:${zt}`,resorts:[s.device_id]}}:null}}));const Rt=r`.card-config{display:flex;flex-direction:column;gap:12px}.group{border:1px solid var(--divider-color);border-radius:var(--ha-card-border-radius, 12px);margin-top:0;padding:16px}.group-header{color:var(--primary-text-color);font-size:16px;font-weight:500;margin-bottom:12px}ha-form{display:block}`;function Dt(t){return"string"==typeof t?t:t.device}const Lt=[{name:"title",selector:{text:{}}},{name:"resorts",selector:{device:{multiple:!0,integration:"bergfex"}}},{type:"expandable",title:"groups.display",schema:[{name:"show_conditions",selector:{boolean:{}}},{name:"conditions_default_open",selector:{boolean:{}}},{name:"show_trend",selector:{boolean:{}}},{name:"show_link",selector:{boolean:{}}},{name:"show_last_updated",selector:{boolean:{}}},{name:"hide_closed_resorts",selector:{boolean:{}}},{name:"sort_by",selector:{select:{mode:"dropdown"}}}]},{type:"expandable",title:"groups.cross_country_only",schema:[{name:"show_trails",selector:{boolean:{}}}]},{type:"expandable",title:"groups.ski_only",schema:[{name:"show_snow",selector:{boolean:{}}},{name:"show_lifts_slopes",selector:{boolean:{}}},{name:"show_forecast",selector:{boolean:{}}},{name:"forecast_default_open",selector:{boolean:{}}}]}],Ut="bergfex-card-editor";class Ft extends ct{setConfig(t){this._config=t}_helper(t){const e=`component.bergfex-card.editor.${t}_helper`,s=At(this.hass,e);return s===e?void 0:s}_valueChanged(t){if(!this.hass||!this._config)return;const e={...t.detail.value};if(Array.isArray(e.resorts)){const t=new Map;for(const e of this._config.resorts??[])e&&"object"==typeof e&&e.name&&t.set(e.device,e.name);e.resorts=e.resorts.filter(t=>Boolean(t)&&Boolean(Dt(t))).map(e=>{const s=Dt(e),i=t.get(s);return i?{device:s,name:i}:s})}Nt(this,"config-changed",{config:ft({...this._config,...e})})}render(){if(!this.hass||!this._config)return W``;const t=[{value:"mountain",label:At(this.hass,"component.bergfex-card.editor.sort_by_options.mountain")},{value:"valley",label:At(this.hass,"component.bergfex-card.editor.sort_by_options.valley")},{value:"new",label:At(this.hass,"component.bergfex-card.editor.sort_by_options.new")},{value:"lift",label:At(this.hass,"component.bergfex-card.editor.sort_by_options.lift")},{value:"classical",label:At(this.hass,"component.bergfex-card.editor.sort_by_options.classical")},{value:"skating",label:At(this.hass,"component.bergfex-card.editor.sort_by_options.skating")},{value:"update",label:At(this.hass,"component.bergfex-card.editor.sort_by_options.update")}],e=(e=>e.reduce((e,s)=>{const i={...s};if("expandable"===i.type&&Array.isArray(i.schema)){const s=i.schema.map(t=>({...t}));return"groups.display"===i.title&&s.forEach(e=>{"sort_by"===e.name&&(e.selector={select:{mode:"dropdown",clearable:!0,options:t}})}),i.title="string"==typeof i.title?At(this.hass,`component.bergfex-card.editor.${i.title}`):i.title,i.schema=s,e.push(i),e}return"resorts"===i.name&&(i.selector={device:{multiple:!0,integration:"bergfex"}}),e.push(i),e},[]))(Lt),s={..._t,...this._config,resorts:(this._config.resorts??[]).filter(Boolean).map(Dt)};return W`
      <ha-card>
        <div class="card-content card-config">
          <ha-form
            .schema=${e}
            .hass=${this.hass}
            .data=${s}
            .computeLabel=${t=>At(this.hass,`component.bergfex-card.editor.${t.name}`)}
            .computeHelper=${t=>this._helper(t.name)}
            @value-changed=${this._valueChanged}
          ></ha-form>
        </div>
      </ha-card>
    `}static{this.styles=r`
    ${a(Rt)}
  `}}t([pt({attribute:!1})],Ft.prototype,"hass",void 0),t([ut()],Ft.prototype,"_config",void 0),customElements.get(Ut)||customElements.define(Ut,Ft);var It=Object.freeze({__proto__:null,BergfexCardEditor:Ft});export{Mt as BergfexCard};
