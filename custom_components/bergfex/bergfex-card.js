function e(e,t,s,i){var o,n=arguments.length,a=n<3?t:null===i?i=Object.getOwnPropertyDescriptor(t,s):i;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)a=Reflect.decorate(e,t,s,i);else for(var r=e.length-1;r>=0;r--)(o=e[r])&&(a=(n<3?o(a):n>3?o(t,s,a):o(t,s))||a);return n>3&&a&&Object.defineProperty(t,s,a),a}console.groupCollapsed("%c🏔️ BERGFEX CARD%cv3.0.1","color: orange; font-weight: bold; background: black; padding: 2px 4px; border-radius: 2px 0 0 2px;","color: white; font-weight: bold; background: dimgray; padding: 2px 4px; border-radius: 0 2px 2px 0;"),console.info("A Lovelace card to display ski resort conditions from Bergfex."),console.info("Github:  https://github.com/timmaurice/bergfex.git"),console.info("Sponsor: https://buymeacoffee.com/timmaurice"),console.groupEnd(),"function"==typeof SuppressedError&&SuppressedError;
/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t=globalThis,s=t.ShadowRoot&&(void 0===t.ShadyCSS||t.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),o=new WeakMap;let n=class{constructor(e,t,s){if(this._$cssResult$=!0,s!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(s&&void 0===e){const s=void 0!==t&&1===t.length;s&&(e=o.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),s&&o.set(t,e))}return e}toString(){return this.cssText}};const a=e=>new n("string"==typeof e?e:e+"",void 0,i),r=(e,...t)=>{const s=1===e.length?e[0]:t.reduce((t,s,i)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+e[i+1],e[0]);return new n(s,e,i)},l=s?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const s of e.cssRules)t+=s.cssText;return a(t)})(e):e,{is:c,defineProperty:d,getOwnPropertyDescriptor:h,getOwnPropertyNames:p,getOwnPropertySymbols:u,getPrototypeOf:_}=Object,m=globalThis,f=m.trustedTypes,g=f?f.emptyScript:"",v=m.reactiveElementPolyfillSupport,w=(e,t)=>e,y={toAttribute(e,t){switch(t){case Boolean:e=e?g:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let s=e;switch(t){case Boolean:s=null!==e;break;case Number:s=null===e?null:Number(e);break;case Object:case Array:try{s=JSON.parse(e)}catch(e){s=null}}return s}},b=(e,t)=>!c(e,t),$={attribute:!0,type:String,converter:y,reflect:!1,useDefault:!1,hasChanged:b};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */Symbol.metadata??=Symbol("metadata"),m.litPropertyMetadata??=new WeakMap;let k=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=$){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const s=Symbol(),i=this.getPropertyDescriptor(e,s,t);void 0!==i&&d(this.prototype,e,i)}}static getPropertyDescriptor(e,t,s){const{get:i,set:o}=h(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:i,set(t){const n=i?.call(this);o?.call(this,t),this.requestUpdate(e,n,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??$}static _$Ei(){if(this.hasOwnProperty(w("elementProperties")))return;const e=_(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(w("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(w("properties"))){const e=this.properties,t=[...p(e),...u(e)];for(const s of t)this.createProperty(s,e[s])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,s]of t)this.elementProperties.set(e,s)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const s=this._$Eu(e,t);void 0!==s&&this._$Eh.set(s,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const s=new Set(e.flat(1/0).reverse());for(const e of s)t.unshift(l(e))}else void 0!==e&&t.push(l(e));return t}static _$Eu(e,t){const s=t.attribute;return!1===s?void 0:"string"==typeof s?s:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const s of t.keys())this.hasOwnProperty(s)&&(e.set(s,this[s]),delete this[s]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((e,i)=>{if(s)e.adoptedStyleSheets=i.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const s of i){const i=document.createElement("style"),o=t.litNonce;void 0!==o&&i.setAttribute("nonce",o),i.textContent=s.cssText,e.appendChild(i)}})(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,s){this._$AK(e,s)}_$ET(e,t){const s=this.constructor.elementProperties.get(e),i=this.constructor._$Eu(e,s);if(void 0!==i&&!0===s.reflect){const o=(void 0!==s.converter?.toAttribute?s.converter:y).toAttribute(t,s.type);this._$Em=e,null==o?this.removeAttribute(i):this.setAttribute(i,o),this._$Em=null}}_$AK(e,t){const s=this.constructor,i=s._$Eh.get(e);if(void 0!==i&&this._$Em!==i){const e=s.getPropertyOptions(i),o="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:y;this._$Em=i;const n=o.fromAttribute(t,e.type);this[i]=n??this._$Ej?.get(i)??n,this._$Em=null}}requestUpdate(e,t,s,i=!1,o){if(void 0!==e){const n=this.constructor;if(!1===i&&(o=this[e]),s??=n.getPropertyOptions(e),!((s.hasChanged??b)(o,t)||s.useDefault&&s.reflect&&o===this._$Ej?.get(e)&&!this.hasAttribute(n._$Eu(e,s))))return;this.C(e,t,s)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:s,reflect:i,wrapped:o},n){s&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,n??t??this[e]),!0!==o||void 0!==n)||(this._$AL.has(e)||(this.hasUpdated||s||(t=void 0),this._$AL.set(e,t)),!0===i&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,s]of e){const{wrapped:e}=s,i=this[t];!0!==e||this._$AL.has(t)||void 0===i||this.C(t,void 0,s,i)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};k.elementStyles=[],k.shadowRootOptions={mode:"open"},k[w("elementProperties")]=new Map,k[w("finalized")]=new Map,v?.({ReactiveElement:k}),(m.reactiveElementVersions??=[]).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const x=globalThis,S=e=>e,A=x.trustedTypes,N=A?A.createPolicy("lit-html",{createHTML:e=>e}):void 0,C="$lit$",z=`lit$${Math.random().toFixed(9).slice(2)}$`,P="?"+z,j=`<${P}>`,E=document,T=()=>E.createComment(""),O=e=>null===e||"object"!=typeof e&&"function"!=typeof e,M=Array.isArray,R="[ \t\n\f\r]",D=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,L=/-->/g,F=/>/g,U=RegExp(`>|${R}(?:([^\\s"'>=/]+)(${R}*=${R}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),B=/'/g,I=/"/g,H=/^(?:script|style|textarea|title)$/i,W=(e=>(t,...s)=>({_$litType$:e,strings:t,values:s}))(1),V=Symbol.for("lit-noChange"),q=Symbol.for("lit-nothing"),K=new WeakMap,G=E.createTreeWalker(E,129);function Z(e,t){if(!M(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==N?N.createHTML(t):t}const J=(e,t)=>{const s=e.length-1,i=[];let o,n=2===t?"<svg>":3===t?"<math>":"",a=D;for(let t=0;t<s;t++){const s=e[t];let r,l,c=-1,d=0;for(;d<s.length&&(a.lastIndex=d,l=a.exec(s),null!==l);)d=a.lastIndex,a===D?"!--"===l[1]?a=L:void 0!==l[1]?a=F:void 0!==l[2]?(H.test(l[2])&&(o=RegExp("</"+l[2],"g")),a=U):void 0!==l[3]&&(a=U):a===U?">"===l[0]?(a=o??D,c=-1):void 0===l[1]?c=-2:(c=a.lastIndex-l[2].length,r=l[1],a=void 0===l[3]?U:'"'===l[3]?I:B):a===I||a===B?a=U:a===L||a===F?a=D:(a=U,o=void 0);const h=a===U&&e[t+1].startsWith("/>")?" ":"";n+=a===D?s+j:c>=0?(i.push(r),s.slice(0,c)+C+s.slice(c)+z+h):s+z+(-2===c?t:h)}return[Z(e,n+(e[s]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),i]};class Y{constructor({strings:e,_$litType$:t},s){let i;this.parts=[];let o=0,n=0;const a=e.length-1,r=this.parts,[l,c]=J(e,t);if(this.el=Y.createElement(l,s),G.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(i=G.nextNode())&&r.length<a;){if(1===i.nodeType){if(i.hasAttributes())for(const e of i.getAttributeNames())if(e.endsWith(C)){const t=c[n++],s=i.getAttribute(e).split(z),a=/([.?@])?(.*)/.exec(t);r.push({type:1,index:o,name:a[2],strings:s,ctor:"."===a[1]?se:"?"===a[1]?ie:"@"===a[1]?oe:te}),i.removeAttribute(e)}else e.startsWith(z)&&(r.push({type:6,index:o}),i.removeAttribute(e));if(H.test(i.tagName)){const e=i.textContent.split(z),t=e.length-1;if(t>0){i.textContent=A?A.emptyScript:"";for(let s=0;s<t;s++)i.append(e[s],T()),G.nextNode(),r.push({type:2,index:++o});i.append(e[t],T())}}}else if(8===i.nodeType)if(i.data===P)r.push({type:2,index:o});else{let e=-1;for(;-1!==(e=i.data.indexOf(z,e+1));)r.push({type:7,index:o}),e+=z.length-1}o++}}static createElement(e,t){const s=E.createElement("template");return s.innerHTML=e,s}}function Q(e,t,s=e,i){if(t===V)return t;let o=void 0!==i?s._$Co?.[i]:s._$Cl;const n=O(t)?void 0:t._$litDirective$;return o?.constructor!==n&&(o?._$AO?.(!1),void 0===n?o=void 0:(o=new n(e),o._$AT(e,s,i)),void 0!==i?(s._$Co??=[])[i]=o:s._$Cl=o),void 0!==o&&(t=Q(e,o._$AS(e,t.values),o,i)),t}class X{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:s}=this._$AD,i=(e?.creationScope??E).importNode(t,!0);G.currentNode=i;let o=G.nextNode(),n=0,a=0,r=s[0];for(;void 0!==r;){if(n===r.index){let t;2===r.type?t=new ee(o,o.nextSibling,this,e):1===r.type?t=new r.ctor(o,r.name,r.strings,this,e):6===r.type&&(t=new ne(o,this,e)),this._$AV.push(t),r=s[++a]}n!==r?.index&&(o=G.nextNode(),n++)}return G.currentNode=E,i}p(e){let t=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(e,s,t),t+=s.strings.length-2):s._$AI(e[t])),t++}}class ee{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,s,i){this.type=2,this._$AH=q,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=Q(this,e,t),O(e)?e===q||null==e||""===e?(this._$AH!==q&&this._$AR(),this._$AH=q):e!==this._$AH&&e!==V&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>M(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==q&&O(this._$AH)?this._$AA.nextSibling.data=e:this.T(E.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:s}=e,i="number"==typeof s?this._$AC(e):(void 0===s.el&&(s.el=Y.createElement(Z(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(t);else{const e=new X(i,this),s=e.u(this.options);e.p(t),this.T(s),this._$AH=e}}_$AC(e){let t=K.get(e.strings);return void 0===t&&K.set(e.strings,t=new Y(e)),t}k(e){M(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let s,i=0;for(const o of e)i===t.length?t.push(s=new ee(this.O(T()),this.O(T()),this,this.options)):s=t[i],s._$AI(o),i++;i<t.length&&(this._$AR(s&&s._$AB.nextSibling,i),t.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=S(e).nextSibling;S(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class te{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,s,i,o){this.type=1,this._$AH=q,this._$AN=void 0,this.element=e,this.name=t,this._$AM=i,this.options=o,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=q}_$AI(e,t=this,s,i){const o=this.strings;let n=!1;if(void 0===o)e=Q(this,e,t,0),n=!O(e)||e!==this._$AH&&e!==V,n&&(this._$AH=e);else{const i=e;let a,r;for(e=o[0],a=0;a<o.length-1;a++)r=Q(this,i[s+a],t,a),r===V&&(r=this._$AH[a]),n||=!O(r)||r!==this._$AH[a],r===q?e=q:e!==q&&(e+=(r??"")+o[a+1]),this._$AH[a]=r}n&&!i&&this.j(e)}j(e){e===q?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class se extends te{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===q?void 0:e}}class ie extends te{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==q)}}class oe extends te{constructor(e,t,s,i,o){super(e,t,s,i,o),this.type=5}_$AI(e,t=this){if((e=Q(this,e,t,0)??q)===V)return;const s=this._$AH,i=e===q&&s!==q||e.capture!==s.capture||e.once!==s.once||e.passive!==s.passive,o=e!==q&&(s===q||i);i&&this.element.removeEventListener(this.name,this,s),o&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class ne{constructor(e,t,s){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(e){Q(this,e)}}const ae=x.litHtmlPolyfillSupport;ae?.(Y,ee),(x.litHtmlVersions??=[]).push("3.3.3");const re=globalThis;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */let le=class extends k{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,s)=>{const i=s?.renderBefore??t;let o=i._$litPart$;if(void 0===o){const e=s?.renderBefore??null;i._$litPart$=o=new ee(t.insertBefore(T(),e),e,void 0,s??{})}return o._$AI(e),o})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return V}};le._$litElement$=!0,le.finalized=!0,re.litElementHydrateSupport?.({LitElement:le});const ce=re.litElementPolyfillSupport;ce?.({LitElement:le}),(re.litElementVersions??=[]).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const de={attribute:!0,type:String,converter:y,reflect:!1,hasChanged:b},he=(e=de,t,s)=>{const{kind:i,metadata:o}=s;let n=globalThis.litPropertyMetadata.get(o);if(void 0===n&&globalThis.litPropertyMetadata.set(o,n=new Map),"setter"===i&&((e=Object.create(e)).wrapped=!0),n.set(s.name,e),"accessor"===i){const{name:i}=s;return{set(s){const o=t.get.call(this);t.set.call(this,s),this.requestUpdate(i,o,e,!0,s)},init(t){return void 0!==t&&this.C(i,void 0,e,t),t}}}if("setter"===i){const{name:i}=s;return function(s){const o=this[i];t.call(this,s),this.requestUpdate(i,o,e,!0,s)}}throw Error("Unsupported decorator location: "+i)};function pe(e){return(t,s)=>"object"==typeof s?he(e,t,s):((e,t,s)=>{const i=t.hasOwnProperty(s);return t.constructor.createProperty(s,e),i?Object.getOwnPropertyDescriptor(t,s):void 0})(e,t,s)}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function ue(e){return pe({...e,state:!0,attribute:!1})}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const _e={show_snow:!0,show_lifts_slopes:!0,show_trails:!0,show_conditions:!0,show_forecast:!1,show_trend:!1,show_link:!0,show_last_updated:!0,hide_closed_resorts:!1,conditions_default_open:!1,forecast_default_open:!1};function me(e){const t={...e};for(const[e,s]of Object.entries(_e))t[e]===s&&delete t[e];for(const e of["title","sort_by"]){const s=t[e];void 0!==s&&""!==s&&"none"!==s||delete t[e]}return t}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const fe=1,ge=2,ve=e=>(...t)=>({_$litDirective$:e,values:t});class we{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,s){this._$Ct=e,this._$AM=t,this._$Ci=s}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}}
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const ye=ve(class extends we{constructor(e){if(super(e),e.type!==fe||"class"!==e.name||e.strings?.length>2)throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.")}render(e){return" "+Object.keys(e).filter(t=>e[t]).join(" ")+" "}update(e,[t]){if(void 0===this.st){this.st=new Set,void 0!==e.strings&&(this.nt=new Set(e.strings.join(" ").split(/\s/).filter(e=>""!==e)));for(const e in t)t[e]&&!this.nt?.has(e)&&this.st.add(e);return this.render(t)}const s=e.element.classList;for(const e of this.st)e in t||(s.remove(e),this.st.delete(e));for(const e in t){const i=!!t[e];i===this.st.has(e)||this.nt?.has(e)||(i?(s.add(e),this.st.add(e)):(s.remove(e),this.st.delete(e)))}return V}});
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */class be extends we{constructor(e){if(super(e),this.it=q,e.type!==ge)throw Error(this.constructor.directiveName+"() can only be used in child bindings")}render(e){if(e===q||null==e)return this._t=void 0,this.it=e;if(e===V)return e;if("string"!=typeof e)throw Error(this.constructor.directiveName+"() called with a non-string value");if(e===this.it)return this._t;this.it=e;const t=[e];return t.raw=t,this._t={_$litType$:this.constructor.resultType,strings:t,values:[]}}}be.directiveName="unsafeHTML",be.resultType=1;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
class $e extends be{}$e.directiveName="unsafeSVG",$e.resultType=2;const ke=ve($e);const xe={da:{editor:{groups:{core:"Kerne Konfiguration",display:"Visning",ski_only:"Skiområde muligheder",cross_country_only:"Indstillinger for langrend"},title:"Title (Valgfri)",resorts:"Område enheder",show_snow:"Vis sne information",show_lifts_slopes:"Vis lift & piste statistik",show_conditions:"Vis forholds sektion",conditions_default_open:"Forholds sektion udvidet som standard",show_forecast:"Vis sne udsigt",forecast_default_open:"Sne udsigt udvidet som standard",show_trend:"Vis trend indikatorer (24h)",show_last_updated:"Vis sidst opdateret",show_link:"Vis link ikon",hide_closed_resorts:"Skjul lukkede områder",hide_closed_resorts_helper:"Skjuler kun skisportssteder mellem vinter- og sommersæsonen. Steder i sommerdrift forbliver synlige, selv om man ikke kan stå på ski.",sort_by:"Sorter efter",sort_by_options:{mountain:"Sne (Bjerg)",valley:"Sne (Dal)",new:"Ny sne",lift:"Lifter åbne",classical:"Klassiske stier",skating:"Skate stier",update:"Sidste opdatering"},show_trails:"Vis løjpestatistik"},card:{resort_not_found:"Områder ikke fundet: {resort}",lifts_open:"Lifter",header:{snow_mountain:"Bjerg",snow_valley:"Dal",new_snow:"Ny",snow_condition:"Sne forhold",slope_condition:"Piste forhold",avalanche_warning:"Lavine advarsel",last_snowfall:"Sidste snefald",slopes_info:"Pister",slopes_info_km:"Pister (km)",slopes_open_km:"Åben",slopes_total:"Total",classical_trails:"Klassiske stier",skating_trails:"Skate stier",classical_condition:"Klassisk forhold",skating_condition:"Skate forhold",operation_status:"Driftsstatus",link_title:"Åben {resortName} detaljeret side på bergfex"},forecast:{daily:"Daglig",summary:"Opsummeret",hour:"{hours} Timer",today:"I dag",tomorrow:"I morgen"},accordion:{conditions:"Forhold",forecast:"Sne udsigt"},status:{open:"Åben",closed:"Lukket",unknown:"Ukendt",winter_season:"Vintersæson",summer_season:"Sommersæson",season_from:"fra {date}",season_last_year:"sidste år: {date}"},warnings:{not_found:"Skisportsstedet blev ikke fundet: {subject}",unavailable:"Der rapporteres ingen data for {subject}.",wrong_domain:"{subject} er en {actual}-enhed, men der kræves en {expected}.",not_numeric:'{subject} rapporterer ikke et tal (værdien er "{state}").'}},common:{errors:{no_resorts:"Du skal definere mindst én feriestedsenhed."}}},de:{editor:{groups:{core:"Grundeinstellungen",display:"Anzeige",ski_only:"Optionen für Skigebiete",cross_country_only:"Optionen für Loipengebiete"},title:"Titel (Optional)",resorts:"Skigebiete",show_snow:"Schneeinformationen anzeigen",show_lifts_slopes:"Lift- & Pistenstatistiken anzeigen",show_conditions:"Bedingungen anzeigen",conditions_default_open:"Bedingungen standardmäßig ausgeklappt",show_forecast:"Schneevorhersage anzeigen",forecast_default_open:"Schneevorhersage standardmäßig ausgeklappt",show_trend:"Trend-Indikatoren anzeigen (24h)",show_last_updated:"Zuletzt aktualisiert anzeigen",show_link:"Link-Symbol anzeigen",hide_closed_resorts:"Geschlossene Skigebiete ausblenden",hide_closed_resorts_helper:"Blendet nur Skigebiete aus, die zwischen Winter- und Sommersaison liegen. Gebiete im Sommerbetrieb bleiben sichtbar, auch wenn nicht Ski gefahren werden kann.",sort_by:"Sortieren nach",sort_by_options:{mountain:"Schnee (Berg)",valley:"Schnee (Tal)",new:"Neuschnee",lift:"Offene Lifte",classical:"Klassische Loipen",skating:"Skating-Loipen",update:"Letzte Aktualisierung"},show_trails:"Loipenstatistiken anzeigen"},card:{resort_not_found:"Skigebiet nicht gefunden: {resort}",lifts_open:"Lifte",header:{snow_mountain:"Berg",snow_valley:"Tal",new_snow:"Neu",snow_condition:"Schneezustand",slope_condition:"Pistenzustand",avalanche_warning:"Lawinenwarnstufe",last_snowfall:"Letzter Schneefall",slopes_info:"Pisten",slopes_info_km:"Pisten (km)",slopes_open_km:"Offen",slopes_total:"Gesamt",classical_trails:"Klassische Loipen",skating_trails:"Skating-Loipen",classical_condition:"Klassischer Zustand",skating_condition:"Skating-Zustand",operation_status:"Betriebsstatus",link_title:"{resortName} Detailseite auf bergfex öffnen"},forecast:{daily:"Täglich",summary:"Zusammenfassung",hour:"{hours} Stunden",today:"Heute",tomorrow:"Morgen"},accordion:{conditions:"Bedingungen",forecast:"Schneevorhersage"},status:{open:"Offen",closed:"Geschlossen",unknown:"Unbekannt",winter_season:"Wintersaison",summer_season:"Sommersaison",season_from:"ab {date}",season_last_year:"letztes Jahr: {date}"},warnings:{not_found:"Skigebiet nicht gefunden: {subject}",unavailable:"Für {subject} werden keine Daten gemeldet.",wrong_domain:"{subject} ist eine {actual}-Entität, benötigt wird eine {expected}.",not_numeric:"{subject} meldet keine Zahl (der Wert ist „{state}“)."}},common:{errors:{no_resorts:"Sie müssen mindestens ein Skigebiet definieren."}}},en:{editor:{groups:{core:"Core Configuration",display:"Display",ski_only:"Ski Resort Options",cross_country_only:"Cross-country options"},title:"Title (Optional)",resorts:"Resort Entities",show_snow:"Show snow information",show_lifts_slopes:"Show lift & slope statistics",show_conditions:"Show conditions section",conditions_default_open:"Conditions section expanded by default",show_forecast:"Show snow forecast",forecast_default_open:"Snow forecast expanded by default",show_trend:"Show trend indicators (24h)",show_last_updated:"Show last updated",show_link:"Show link icon",hide_closed_resorts:"Hide closed resorts",hide_closed_resorts_helper:"Only hides resorts between the winter and summer seasons. Resorts in summer operation stay visible, even though you cannot ski there.",sort_by:"Sort by",sort_by_options:{mountain:"Snow (Mountain)",valley:"Snow (Valley)",new:"New Snow",lift:"Lifts Open",classical:"Classical Trails",skating:"Skating Trails",update:"Last Update"},show_trails:"Show trail statistics"},card:{resort_not_found:"Resort not found: {resort}",lifts_open:"Lifts",header:{snow_mountain:"Mountain",snow_valley:"Valley",new_snow:"New",snow_condition:"Snow Condition",slope_condition:"Slope Condition",avalanche_warning:"Avalanche Warning",last_snowfall:"Last Snowfall",slopes_info:"Slopes",slopes_info_km:"Slopes (km)",slopes_open_km:"Open",slopes_total:"Total",classical_trails:"Classical Trails",skating_trails:"Skating Trails",classical_condition:"Classical Condition",skating_condition:"Skating Condition",operation_status:"Operation Status",link_title:"Open {resortName} detail page on bergfex"},forecast:{daily:"Daily",summary:"Summary",hour:"{hours} Hours",today:"Today",tomorrow:"Tomorrow"},accordion:{conditions:"Conditions",forecast:"Snow Forecast"},status:{open:"Open",closed:"Closed",unknown:"Unknown",winter_season:"Winter season",summer_season:"Summer season",season_from:"from {date}",season_last_year:"last year: {date}"},warnings:{not_found:"Resort not found: {subject}",unavailable:"No data is being reported for {subject}.",wrong_domain:"{subject} is a {actual} entity, but a {expected} is needed.",not_numeric:'{subject} does not report a number (it reads "{state}").'}},common:{errors:{no_resorts:"You need to define at least one resort entity."}}},es:{editor:{groups:{core:"Configuración principal",display:"Visualización",ski_only:"Opciones de estación de esquí",cross_country_only:"Opciones de esquí de fondo"},title:"Título (opcional)",resorts:"Estaciones",show_snow:"Mostrar información de nieve",show_lifts_slopes:"Mostrar estadísticas de remontes y pistas",show_conditions:"Mostrar la sección de condiciones",conditions_default_open:"Sección de condiciones desplegada por defecto",show_forecast:"Mostrar previsión de nieve",forecast_default_open:"Previsión de nieve desplegada por defecto",show_trend:"Mostrar indicadores de tendencia (24 h)",show_last_updated:"Mostrar última actualización",show_link:"Mostrar icono de enlace",hide_closed_resorts:"Ocultar estaciones cerradas",hide_closed_resorts_helper:"Solo oculta las estaciones entre la temporada de invierno y la de verano. Las estaciones en operación de verano siguen visibles, aunque no se pueda esquiar en ellas.",sort_by:"Ordenar por",sort_by_options:{mountain:"Nieve (montaña)",valley:"Nieve (valle)",new:"Nieve nueva",lift:"Remontes abiertos",classical:"Pistas clásicas",skating:"Pistas de patinador",update:"Última actualización"},show_trails:"Mostrar estadísticas de pistas"},card:{resort_not_found:"Estación no encontrada: {resort}",lifts_open:"Remontes",header:{snow_mountain:"Montaña",snow_valley:"Valle",new_snow:"Nueva",snow_condition:"Estado de la nieve",slope_condition:"Estado de las pistas",avalanche_warning:"Riesgo de aludes",last_snowfall:"Última nevada",slopes_info:"Pistas",slopes_info_km:"Pistas (km)",slopes_open_km:"Abiertas",slopes_total:"Total",classical_trails:"Pistas clásicas",skating_trails:"Pistas de patinador",classical_condition:"Estado del clásico",skating_condition:"Estado del patinador",operation_status:"Estado de operación",link_title:"Abrir la página de {resortName} en bergfex"},forecast:{daily:"Diaria",summary:"Resumen",hour:"{hours} horas",today:"Hoy",tomorrow:"Mañana"},accordion:{conditions:"Condiciones",forecast:"Previsión de nieve"},status:{open:"Abierta",closed:"Cerrada",unknown:"Desconocido",winter_season:"Temporada de invierno",summer_season:"Temporada de verano",season_from:"desde el {date}",season_last_year:"el año pasado: {date}"},warnings:{not_found:"Estación no encontrada: {subject}",unavailable:"No se están recibiendo datos de {subject}.",wrong_domain:"{subject} es una entidad {actual}, pero se necesita una {expected}.",not_numeric:"{subject} no devuelve un número (su valor es «{state}»)."}},common:{errors:{no_resorts:"Debes definir al menos una estación."}}},fr:{editor:{groups:{core:"Configuration",display:"Affichage",ski_only:"Options station de ski",cross_country_only:"Options pour le ski de fond"},title:"Titre (optionnel)",resorts:"Stations de ski",show_snow:"Afficher les info sur la neige",show_lifts_slopes:"Afficher statistiques remontées & pistes",show_conditions:"Afficher la section des conditions",conditions_default_open:"Section conditions développée par défaut",show_forecast:"Afficher les prévisions de neige",forecast_default_open:"Prévisions de neige développées par défaut",show_trend:"Afficher les tendances (24 h)",show_last_updated:"Afficher la dernière mise à jour",show_link:"Afficher le lien",hide_closed_resorts:"Masquer les stations fermées",hide_closed_resorts_helper:"Masque uniquement les stations situées entre la saison d'hiver et celle d'été. Les stations en exploitation estivale restent visibles, même si le ski y est impossible.",sort_by:"Trier par",sort_by_options:{mountain:"Neige (au sommet)",valley:"Neige (dans la vallée)",new:"Dernière chute de neige",lift:"Remontées ouvertes",classical:"Pistes classiques",skating:"Back-country",update:"Dernière mise à jour"},show_trails:"Afficher les statistiques de pistes"},card:{resort_not_found:"Station non trouvée : {resort}",lifts_open:"Remontées ouvertes",header:{snow_mountain:"Sommet",snow_valley:"Vallée",new_snow:"Dernière chute de neige",snow_condition:"État de la neige",slope_condition:"État des pistes",avalanche_warning:"Risque avalanche",last_snowfall:"Dernière chute de neige",slopes_info:"Pistes",slopes_info_km:"Pistes (km)",slopes_open_km:"Ouvertes",slopes_total:"Total",classical_trails:"Pistes classiques",skating_trails:"Pistes de skating",classical_condition:"État classique",skating_condition:"État backcountry",operation_status:"Statut",link_title:"Ouvrir la page bergfex de {resortName}"},forecast:{daily:"Quotidien",summary:"Résumé",hour:"{hours} heure(s)",today:"Aujourd’hui",tomorrow:"Demain"},accordion:{conditions:"Conditions",forecast:"Prévisions de neige"},status:{open:"Ouvert",closed:"Fermé",unknown:"Inconnu",winter_season:"Saison hivernale",summer_season:"Saison estivale",season_from:"à partir du {date}",season_last_year:"l'an dernier : {date}"},warnings:{not_found:"Station introuvable : {subject}",unavailable:"Aucune donnée n’est remontée pour {subject}.",wrong_domain:"{subject} est une entité {actual}, mais une entité {expected} est attendue.",not_numeric:"{subject} ne renvoie pas de nombre (la valeur est « {state} »)."}},common:{errors:{no_resorts:"Vous devez définir au moins une station de ski."}}},it:{editor:{groups:{core:"Configurazione principale",display:"Visualizzazione",ski_only:"Opzioni comprensorio sciistico",cross_country_only:"Opzioni sci di fondo"},title:"Titolo (facoltativo)",resorts:"Comprensori",show_snow:"Mostra le informazioni sulla neve",show_lifts_slopes:"Mostra le statistiche di impianti e piste",show_conditions:"Mostra la sezione condizioni",conditions_default_open:"Sezione condizioni aperta per impostazione predefinita",show_forecast:"Mostra le previsioni di neve",forecast_default_open:"Previsioni di neve aperte per impostazione predefinita",show_trend:"Mostra gli indicatori di tendenza (24 h)",show_last_updated:"Mostra ultimo aggiornamento",show_link:"Mostra l'icona del collegamento",hide_closed_resorts:"Nascondi i comprensori chiusi",hide_closed_resorts_helper:"Nasconde solo i comprensori tra la stagione invernale e quella estiva. I comprensori in esercizio estivo restano visibili, anche se non vi si può sciare.",sort_by:"Ordina per",sort_by_options:{mountain:"Neve (monte)",valley:"Neve (valle)",new:"Neve fresca",lift:"Impianti aperti",classical:"Piste classiche",skating:"Piste skating",update:"Ultimo aggiornamento"},show_trails:"Mostra le statistiche delle piste"},card:{resort_not_found:"Comprensorio non trovato: {resort}",lifts_open:"Impianti",header:{snow_mountain:"Monte",snow_valley:"Valle",new_snow:"Fresca",snow_condition:"Condizioni della neve",slope_condition:"Condizioni delle piste",avalanche_warning:"Pericolo valanghe",last_snowfall:"Ultima nevicata",slopes_info:"Piste",slopes_info_km:"Piste (km)",slopes_open_km:"Aperte",slopes_total:"Totale",classical_trails:"Piste classiche",skating_trails:"Piste skating",classical_condition:"Condizioni classico",skating_condition:"Condizioni skating",operation_status:"Stato di esercizio",link_title:"Apri la pagina di {resortName} su bergfex"},forecast:{daily:"Giornaliera",summary:"Riepilogo",hour:"{hours} ore",today:"Oggi",tomorrow:"Domani"},accordion:{conditions:"Condizioni",forecast:"Previsioni di neve"},status:{open:"Aperto",closed:"Chiuso",unknown:"Sconosciuto",winter_season:"Stagione invernale",summer_season:"Stagione estiva",season_from:"dal {date}",season_last_year:"lo scorso anno: {date}"},warnings:{not_found:"Comprensorio non trovato: {subject}",unavailable:"Non viene riportato alcun dato per {subject}.",wrong_domain:"{subject} è un'entità {actual}, ma ne serve una {expected}.",not_numeric:"{subject} non riporta un numero (il valore è «{state}»)."}},common:{errors:{no_resorts:"Devi definire almeno un comprensorio."}}},nl:{editor:{groups:{core:"Basisconfiguratie",display:"Weergave",ski_only:"Opties voor skigebieden",cross_country_only:"Opties voor langlaufen"},title:"Titel (optioneel)",resorts:"Skigebieden",show_snow:"Sneeuwinformatie tonen",show_lifts_slopes:"Statistieken van liften en pistes tonen",show_conditions:"Sectie met omstandigheden tonen",conditions_default_open:"Sectie met omstandigheden standaard uitgeklapt",show_forecast:"Sneeuwverwachting tonen",forecast_default_open:"Sneeuwverwachting standaard uitgeklapt",show_trend:"Trendindicatoren tonen (24 uur)",show_last_updated:"Laatste update tonen",show_link:"Linkpictogram tonen",hide_closed_resorts:"Gesloten skigebieden verbergen",hide_closed_resorts_helper:"Verbergt alleen skigebieden tussen het winter- en het zomerseizoen. Skigebieden in zomerbedrijf blijven zichtbaar, ook al kun je er niet skiën.",sort_by:"Sorteren op",sort_by_options:{mountain:"Sneeuw (berg)",valley:"Sneeuw (dal)",new:"Verse sneeuw",lift:"Open liften",classical:"Klassieke loipes",skating:"Skatingloipes",update:"Laatste update"},show_trails:"Loipestatistieken tonen"},card:{resort_not_found:"Skigebied niet gevonden: {resort}",lifts_open:"Liften",header:{snow_mountain:"Berg",snow_valley:"Dal",new_snow:"Vers",snow_condition:"Sneeuwconditie",slope_condition:"Pisteconditie",avalanche_warning:"Lawinegevaar",last_snowfall:"Laatste sneeuwval",slopes_info:"Pistes",slopes_info_km:"Pistes (km)",slopes_open_km:"Open",slopes_total:"Totaal",classical_trails:"Klassieke loipes",skating_trails:"Skatingloipes",classical_condition:"Conditie klassiek",skating_condition:"Conditie skating",operation_status:"Bedrijfsstatus",link_title:"Open de pagina van {resortName} op bergfex"},forecast:{daily:"Dagelijks",summary:"Samenvatting",hour:"{hours} uur",today:"Vandaag",tomorrow:"Morgen"},accordion:{conditions:"Omstandigheden",forecast:"Sneeuwverwachting"},status:{open:"Open",closed:"Gesloten",unknown:"Onbekend",winter_season:"Winterseizoen",summer_season:"Zomerseizoen",season_from:"vanaf {date}",season_last_year:"vorig jaar: {date}"},warnings:{not_found:"Skigebied niet gevonden: {subject}",unavailable:"Er worden geen gegevens gemeld voor {subject}.",wrong_domain:"{subject} is een {actual}-entiteit, maar er is een {expected} nodig.",not_numeric:'{subject} meldt geen getal (de waarde is "{state}").'}},common:{errors:{no_resorts:"Je moet minstens één skigebied opgeven."}}},pl:{editor:{groups:{core:"Główna konfiguracja",display:"Wyświetlacz",ski_only:"Opcje kurortu narciarskiego",cross_country_only:"Opcje tras biegowych"},title:"Tytuł (opcjonalnie)",resorts:"Wpisy kurortu",show_snow:"Pokaż informację o śniegu",show_lifts_slopes:"Pokaż statystyki wyciągów i stoków",show_conditions:"Pokaż sekcję warunków",conditions_default_open:"Sekcja warunków domyślnie rozwinięta",show_forecast:"Pokaż prognozę śniegu",forecast_default_open:"Prognoza śniegu domyślnie rozwinięta",show_trend:"Pokaż indykator trendu (24g)",show_last_updated:"Pokaż ostatnio aktualizowane",show_link:"Pokaż ikonę linku",hide_closed_resorts:"Ukryj zamknięte kurorty",hide_closed_resorts_helper:"Ukrywa tylko ośrodki znajdujące się między sezonem zimowym a letnim. Ośrodki w ruchu letnim pozostają widoczne, nawet jeśli nie można w nich jeździć na nartach.",sort_by:"Posortuj",sort_by_options:{mountain:"Śnieg (szczyt)",valley:"Śnieg (dolina)",new:"Nowy śnieg",lift:"Otwarte wyciągi",classical:"Trasy klasyczne",skating:"Trasy łyżwiarskie",update:"Ostatnio aktualizowane"},show_trails:"Pokaż statystyki tras"},card:{resort_not_found:"Nie znaleziono resortu: {resort}",lifts_open:"Wyciągi",header:{snow_mountain:"Szczyt",snow_valley:"Dolina",new_snow:"Nowy opad",snow_condition:"Warunki śniegowe",slope_condition:"Warunki na stoku",avalanche_warning:"Ostrzeżenie lawinowe",last_snowfall:"Ostatni opad",slopes_info:"Trasy",slopes_info_km:"Trasy (km)",slopes_open_km:"Otwarte",slopes_total:"Całkowite",classical_trails:"Trasy klasyczne",skating_trails:"Trasy łyżwiarskie",classical_condition:"Stan tras klasycznych",skating_condition:"Stan tras łyżwiarskich",operation_status:"Status działania",link_title:"Otwórz informację o  {resortName} na stronie Bergfex"},forecast:{daily:"Dzienna",summary:"Podsumowanie",hour:"{hours} godziny",today:"Dziś",tomorrow:"Jutro"},accordion:{conditions:"Warunki",forecast:"Prognoza opadów"},status:{open:"Otwarte",closed:"Zamknięte",unknown:"Nieznany",winter_season:"Sezon zimowy",summer_season:"Sezon letni",season_from:"od {date}",season_last_year:"w zeszłym roku: {date}"},warnings:{not_found:"Nie znaleziono ośrodka: {subject}",unavailable:"Dla {subject} nie są raportowane żadne dane.",wrong_domain:"{subject} to encja {actual}, a wymagana jest {expected}.",not_numeric:"{subject} nie zwraca liczby (wartość to „{state}”)."}},common:{errors:{no_resorts:"Musisz zdefiniować przynajmniej jeden wpis o resorcie."}}}};function Se(e,t){let s=xe[e];for(const e of t){if("object"!=typeof s||null===s)return;s=s[e]}return"string"==typeof s?s:void 0}function Ae(e,t,s={}){const i=e?.language||"en",o=t.replace("component.bergfex-card.","").split("."),n=Se(i,o)??Se("en",o);if("string"==typeof n){let e=n;for(const t in s)e=e.replace(`{${t}}`,String(s[t]));return e}return t}const Ne=(e,t,s,i)=>{const o=new CustomEvent(t,{bubbles:!0,cancelable:!1,composed:!0,...i,detail:s});e.dispatchEvent(o)};function Ce(e){if(null==e||""===e)return null;const t=e instanceof Date?e:new Date(e);return Number.isNaN(t.getTime())?null:t}function ze(e,t){if(null==e||""===e)return"";const s="number"==typeof e?e:parseFloat(e);if(Number.isNaN(s))return String(e);if("none"===t?.locale?.number_format)return String(s);try{return s.toLocaleString(function(e){switch(e?.locale?.number_format){case"comma_decimal":return"en-US";case"decimal_comma":return"de-DE";case"space_comma":return"fr-FR";case"language":return e?.locale?.language||e?.language;case"none":return;default:return e?.language}}(t),{maximumFractionDigits:2})}catch{return String(s)}}function Pe(e,t){const s=Ce(e);if(!s)return"";const i=new Date,o=Math.round((i.getTime()-s.getTime())/1e3);try{const e=new Intl.RelativeTimeFormat(t.language,{numeric:"auto"});if(o<60)return e.format(-o,"second");const s=Math.round(o/60);if(s<60)return e.format(-s,"minute");const i=Math.round(s/60);if(i<24)return e.format(-i,"hour");const n=Math.round(i/24);return e.format(-n,"day")}catch{return function(e,t){const s=Ce(e);if(!s)return"";const i=new Date,o={hour:"numeric",minute:"2-digit"};return s.getDate()===i.getDate()&&s.getMonth()===i.getMonth()&&s.getFullYear()===i.getFullYear()||Object.assign(o,{year:"numeric",month:"short",day:"2-digit"}),"12"===t.locale?.time_format&&(o.hour12=!0),s.toLocaleString(t.language,o)}(e,t)}}const je=r`:host ::slotted(.card-content),.card-content{display:flex;flex-direction:column;gap:12px;padding:16px;overflow-wrap:anywhere}.resort{border:1px solid var(--divider-color);border-radius:var(--ha-card-border-radius, 12px);cursor:pointer;display:flex;flex-direction:column;padding:12px;transition:background-color .2s ease-in-out}.resort:hover{background-color:rgba(var(--rgb-primary-text-color), 0.05)}.resort-header{align-items:center;display:flex;gap:8px;justify-content:space-between}.resort-name{font-size:1.2em;font-weight:500;min-width:0}.resort-status-group{align-items:flex-end;display:flex;flex-direction:column;flex-shrink:0;gap:2px}.season-teaser{color:var(--secondary-text-color);font-size:.75em;white-space:nowrap}.resort-status{background-color:var(--divider-color);border-radius:4px;color:var(--primary-text-color);font-size:.9em;font-weight:500;padding:2px 6px;text-transform:uppercase;white-space:nowrap}.resort-status.open{background-color:var(--label-badge-green)}.resort-status.closed{background-color:var(--label-badge-red)}.resort-status.winter-season{background-color:var(--label-badge-green);opacity:.65}.resort-status.summer-season{background-color:var(--label-badge-yellow);color:rgba(0,0,0,.87)}.details{display:grid;gap:8px;grid-template-columns:repeat(3, minmax(0, 1fr));padding-top:12px}.details.cross-country-details{grid-template-columns:repeat(2, minmax(0, 1fr))}.detail-item{--mdc-icon-size: 24px;align-items:center;cursor:pointer;display:flex;gap:8px}.detail-item ha-icon{color:var(--secondary-text-color)}.detail-item svg,.custom-icon{align-items:center;display:flex;height:var(--mdc-icon-size, 24px);justify-content:center;width:var(--mdc-icon-size, 24px)}.detail-item svg svg,.custom-icon svg{height:100%;width:100%}.detail-item svg.stroke svg,.custom-icon.stroke svg{stroke:var(--secondary-text-color)}.detail-item svg.fill svg,.custom-icon.fill svg{fill:var(--secondary-text-color)}.detail-item-value{align-items:flex-start;display:flex;flex-direction:column;font-size:1.1em;flex:1 1 auto;min-width:0;width:auto}.detail-item-label{color:var(--secondary-text-color);font-size:.8em;max-width:100%;overflow-wrap:anywhere}.detail-item.n-a{opacity:.5}.value-row{align-items:center;display:flex;justify-content:space-between;width:100%}.trend-icon{--mdc-icon-size: 18px;display:inline-block;margin-left:4px;vertical-align:middle}.trend-icon.up{color:var(--label-badge-green, #4caf50)}.trend-icon.down{color:var(--label-badge-red, #f44336)}.trend-icon.same{color:var(--secondary-text-color);opacity:.5}.resort-footer{align-items:center;border-top:1px solid var(--divider-color);display:flex;justify-content:space-between;padding:12px 0 0}.link-icon{color:var(--secondary-text-color);display:flex;text-decoration:none}.last-updated{align-items:center;color:var(--secondary-text-color);cursor:pointer;display:flex;font-size:.8em;gap:4px;justify-content:flex-end}.warning{color:var(--error-color)}.progress-bar-container{background-color:var(--divider-color);border-radius:2px;height:4px;margin-top:4px;overflow:hidden;width:100%}.progress-bar-fill{background-color:var(--primary-color);border-radius:2px;height:100%;transition:width .3s ease-in-out}.accordion-container{border-top:1px solid var(--divider-color);margin-top:12px}.accordion-container+.accordion-container{margin-top:0}.accordion-header{align-items:center;color:var(--primary-text-color);cursor:pointer;display:flex;font-weight:500;justify-content:space-between;padding:12px 0}.accordion-header:hover{background-color:rgba(var(--rgb-primary-text-color), 0.02)}.accordion-content{padding-bottom:12px}.accordion-content.details{grid-template-columns:repeat(2, minmax(0, 1fr))}.forecast-tabs{border-bottom:1px solid var(--divider-color);display:flex;gap:16px;margin-bottom:12px}.forecast-tab{border-bottom:2px solid rgba(0,0,0,0);color:var(--secondary-text-color);cursor:pointer;font-weight:500;padding:8px 12px;transition:all .2s ease}.forecast-tab:hover{color:var(--primary-text-color)}.forecast-tab.active{border-bottom-color:var(--primary-color);color:var(--primary-color)}.forecast-carousel{align-items:center;display:flex;flex-direction:column;gap:8px;position:relative}.forecast-image-container{align-items:center;aspect-ratio:5/3;border-radius:8px;display:flex;justify-content:center;overflow:hidden;position:relative;width:100%}.forecast-image{height:100%;object-fit:contain;width:100%}.carousel-controls{align-items:center;display:flex;justify-content:space-between;margin-top:8px;width:100%}.carousel-btn{align-items:center;background:none;border:none;border-radius:50%;color:var(--primary-text-color);cursor:pointer;display:flex;justify-content:center;padding:8px;transition:background-color .2s}.carousel-btn:hover{background-color:rgba(var(--rgb-primary-text-color), 0.1)}.carousel-btn:disabled{color:var(--disabled-text-color);cursor:not-allowed}.carousel-label{font-size:1.1em;font-weight:500}`;var Ee='<svg height="5.485163mm" viewBox="0 0 5.8208332 5.4851627" width="5.820833mm"\n    xmlns="http://www.w3.org/2000/svg">\n    <g transform="matrix(1.4664468 0 0 1.4664092 -91.591331 -91.904945)">\n        <path\n            d="m65.27 62.689c.183-.037.29-.008.375.088.075.085.084.24.037.339-.053.113-.215.169-.339.157-.104-.01-.229-.082-.256-.183-.038-.142.025-.365.183-.401z" />\n        <path\n            d="m64.248 63.2s.552-.094.803 0c.242.091.585.511.585.511l.365-.365s.139-.043.182 0 0 .183 0 .183l-.365.365-.123.151-.133.032-.365-.292c-.213.103-.45.351-.505.612 0 0 .371.185.483.349.03.043.039.153.039.153l-.093.226-.129.412-.16.512-.256-.182.146-.439.146-.486-.62-.354-.366.438-.384.021-.748-.021v-.292l.895.009.42-.703.511-.584-.234-.034-.569.631s-.097-.012-.124-.047c-.038-.049-.023-.185-.023-.185l.475-.548z" />\n        <path d="m66.06 63.401.129.053-.882 2.595h-.22v-.11z" />\n        <path\n            d="m62.486 63.941 1.199-.077c.042.001.059.003.041.147l-1.241.064c-.042-.003-.017.01.001-.134z" />\n        <path\n            d="m62.494 64.88.677.64s.167.22.332.333c.075.051.27-.023.27-.023.06.146-.023.309-.206.26 0 0-.092-.011-.123-.041-.318-.303-.986-.986-.986-.986z" />\n        <path d="m66.293 65.976c.128-.041.165.02.109.182l-.072.184-.183.072h-2.922l-.11-.219h2.959z" />\n    </g>\n</svg>',Te='<svg height="5.816813mm" viewBox="0 0 5.8207846 5.8168125" width="5.820785mm"\n    xmlns="http://www.w3.org/2000/svg">\n    <path\n        d="m146.23391 74.101876c-1.14758-.322091-2.11388-.608331-2.14733-.636091-.0334-.02776-.0608-.108614-.0608-.179677v-.129205l.0961-.06298.0961-.06298.25793.06981.25792.06982.56924-.595103.56924-.595102.27313-.597014c.15023-.328357.29373-.623828.31889-.656601.0252-.03277.21474-.194992.42129-.360486.20655-.165495.37555-.303341.37556-.306325.00001-.003-.091.000688-.20221.0082l-.20224.01358-.33813.251109c-.18597.13811-.36251.285922-.39232.328472-.0298.04255-.10067.08247-.1575.0887-.0568.0062-.14399-.0072-.19371-.02985-.0497-.02265-.10401-.081-.12064-.129668-.0179-.05241-.35705-.333699-.83186-.689982l-.80161-.601501.012-.08403c.007-.04622.0433-.08999.0815-.09727.0428-.0082.35783.203155.82082.550577.41325.310099.77461.572734.80301.583633.0284.0109.26239-.137376.51998-.329498l.46835-.349314h.75066.75066l.10905.05639c.06.03101.15375.109522.20839.17446.0546.06494.11078.17897.12474.253405.0167.08913.003.19368-.0399.306229l-.0653.170892-.4208.334698c-.23143.184083-.42079.347695-.42079.36358 0 .01589.0834.121276.18544.234202.102.112924.21466.248173.25036.300551l.0649.09523v.588443.588443h.70737.70737l.10149.07983c.0598.04707.10148.118197.10148.173327 0 .05142-.0347.128162-.077.170531l-.077.07703h-1.14378-1.14378l-.59912-.156269c-.32951-.08595-.66539-.173625-.7464-.194837l-.14728-.03857.0461-.05552.0461-.05552h.8662.8662l-.0221-.12518c-.0122-.06885-.0424-.281174-.0673-.471834-.0249-.190659-.0645-.36743-.0881-.392826-.0236-.02539-.17114-.116473-.32784-.202393l-.2849-.156218-.52395.533504c-.28817.293428-.65979.658876-.82581.812106-.16602.153231-.29601.283727-.28888.28999.007.0063.74095.212729 1.6307.45881l1.61771.44742.0674.08163c.0371.04489.0674.11437.0674.154392 0 .04002-.0347.107432-.077.149801-.043.04303-.12379.0752-.18296.07288-.0583-.0023-1.04485-.267685-2.19243-.589775zm2.8867-4.068706c-.0683-.01447-.16944-.05594-.2247-.09215-.0553-.03621-.13332-.138153-.17345-.226536-.0401-.08838-.0733-.202887-.0738-.254455-.00052-.05157.0341-.164231.0768-.25036.0427-.08613.1238-.190098.18027-.231041.0587-.04252.18642-.0807.29795-.08903l.19527-.01459.13481.07378c.0741.04058.17352.141311.22084.223843.0473.08253.0863.210993.0867.285469.00027.07448-.0315.195246-.0707.268379-.0392.07313-.11422.16501-.16667.20417-.0525.03916-.15469.08417-.2272.100019-.0725.01585-.18772.01698-.25604.0025z"\n        stroke-width=".052895" transform="translate(-144.02094 -68.875018)" />\n</svg>';const Oe=["","n/a","unknown","unavailable","none","keine meldung","no information","no info","pas de nouvelle","nessuna comunicazione","nessun messaggio","senza info","no hay información","ningún mensaje","inget meddelande","ingen besked","ei ilmoitusta","nincs üzenet","žádné hlášení","žiadne hlásenie","nema poruke","brez sporočila","ni obvestila","нет сообщений","нет сообщения","fără comunicare","niciun anunţ","no report","geen melding","pas de signalement","pas d'info","aucune information","nessuna segnalazione","sin información","brak komunikatu","nincs jelentés","žádná zpráva","žiadna správa","nema izvješća","ni poročila","нет данных","fără raport","ingen rapport","ingen melding","ei raporttia","pas de rapport","sin informe","brak informacji"],Me="bergfex-card",Re=`${Me}-editor`;class De extends le{constructor(){super(...arguments),this._forecastState={},this._accordionState={},this._historyState={}}setConfig(e){if(!e||!e.resorts||!Array.isArray(e.resorts))throw new Error(Ae(this.hass,"common.errors.no_resorts"));this._config={..._e,...e}}static async getConfigElement(){const e=await window.loadCardHelpers(),t=await e.createCardElement({type:"entities",entities:[]}),s=t?.constructor;return s?.getConfigElement&&await s.getConfigElement(),await Promise.resolve().then(function(){return He}),document.createElement(Re)}static getStubConfig(e,t){const s=De._firstResortDevice(e,t);return{resorts:s?[s]:[]}}static _firstResortDevice(e,t){if(!e?.entities)return;const s=t?.length?t:Object.keys(e.entities);for(const t of s){const s=e.entities[t];if("bergfex"===s?.platform&&s.device_id)return s.device_id}}getCardSize(){const e=this._config?.resorts?.length??0;if(0===e)return 1;let t=2;return this._config.show_snow&&(t+=1),this._config.show_lifts_slopes&&(t+=1),this._config.show_trails&&(t+=1),this._config.show_conditions&&(t+=this._config.conditions_default_open?2:1),this._config.show_forecast&&(t+=this._config.forecast_default_open?3:1),1+e*t}getGridOptions(){return{columns:"full",min_columns:6,rows:"auto",min_rows:2}}_getResorts(e,t){const s={},i=Object.values(e.states);return t.resorts.forEach(t=>{if(!t)return;const o="string"==typeof t?t:t.device,n="object"==typeof t?t.name:void 0,a=function(e,t){const s=t??"";if(!e||!t||!e.devices?.[t])return{ok:!1,problem:{reason:"not_found",subject:s}};const i=Object.values(e.states).filter(s=>e.entities[s.entity_id]?.device_id===t&&(s.entity_id.startsWith("sensor.")||s.entity_id.startsWith("image.")));return 0===i.length?{ok:!1,problem:{reason:"unavailable",subject:s}}:{ok:!0,value:{deviceId:t,entities:i}}}(e,o);if(!a.ok)return void(s[o]={problem:a.problem,name:n});const r=a.value.entities;if(s[o]||(s[o]={forecast_days:[],forecast_summaries:[]}),n&&(s[o].name=n),r.forEach(e=>{const t=e.entity_id;if(t.endsWith("_operation_status"))s[o].operation_status=t;else if(t.endsWith("_status")){s[o].status=t;const i=e.attributes?.link,n=e.attributes?.icon;(i&&i.includes("/langlaufen/")||"mdi:ski-cross-country"===n||"mdi:ski-cross-country-skating"===n)&&(s[o].is_cross_country=!0)}t.endsWith("_snow_valley")&&(s[o].snow_valley=t),t.endsWith("_snow_mountain")&&(s[o].snow_mountain=t),t.endsWith("_new_snow")&&(s[o].new_snow=t),t.endsWith("_lifts_open_count")?s[o].lifts_open_count=t:t.endsWith("_lifts_open")&&!s[o].lifts_open_count&&(s[o].lifts_open=t),t.endsWith("_last_update")&&(s[o].last_update=t),t.endsWith("_snow_condition")&&(s[o].snow_condition=t),t.endsWith("_last_snowfall")&&(s[o].last_snowfall=t),t.endsWith("_avalanche_warning")&&(s[o].avalanche_warning=t),t.endsWith("_slopes_open_km")&&(s[o].slopes_open_km=t),t.endsWith("_slopes_open_count")?s[o].slopes_open_count=t:t.endsWith("_slopes_open")&&!s[o].slopes_open_count&&(s[o].slopes_open=t),t.endsWith("_slope_condition")&&(s[o].slope_condition=t),t.endsWith("_classical_open_km")&&(s[o].classical_trails_open=t),t.endsWith("_skating_open_km")&&(s[o].skating_trails_open=t),t.endsWith("_classical_condition")&&(s[o].classical_condition=t),t.endsWith("_skating_condition")&&(s[o].skating_condition=t),t.includes("_forecast_image_day_")&&s[o].forecast_days?.push(t),t.includes("_summary_image_")&&s[o].forecast_summaries?.push(t)}),s[o].forecast_days=this._usableForecastImages(e,s[o].forecast_days,/day_(\d+)/),s[o].forecast_summaries=this._usableForecastImages(e,s[o].forecast_summaries,/summary_image_(\d+)h/),s[o].forecast_days?.sort(),s[o].forecast_summaries?.sort((e,t)=>{const s=e=>{const t=e.match(/summary_image_(\d+)h/);return t?parseInt(t[1],10):0};return s(e)-s(t)}),!(s[o].forecast_days&&0!==s[o].forecast_days.length||s[o].forecast_summaries&&0!==s[o].forecast_summaries.length)){const e=s[o].status;if(e){const t=e.match(/^sensor\.(.+)_status$/);if(t){const e=`image.${t[1]}_snow_forecast`;i.forEach(t=>{t.entity_id.startsWith(e)&&(t.entity_id.includes("_day_")?s[o].forecast_days?.push(t.entity_id):t.entity_id.includes("_summary_")&&s[o].forecast_summaries?.push(t.entity_id))}),s[o].forecast_days?.sort(),s[o].forecast_summaries?.sort((e,t)=>{const s=e=>{const t=e.match(/summary_(\d+)h/);return t?parseInt(t[1],10):0};return s(e)-s(t)})}}}}),s}shouldUpdate(e){if(this._refreshTrendBaseline(),e.has("_config"))return!0;const t=e.get("hass");if(t){const s=e=>Object.values(this._getResorts(e,this._config)).flatMap(e=>Object.values(e)),i=new Set;for(const e of[...s(this.hass),...s(t)])"string"==typeof e&&i.add(e);const o=[...i].some(e=>t.states[e]!==this.hass.states[e]),n=t.language!==this.hass.language||t.locale?.language!==this.hass.locale?.language||t.locale?.number_format!==this.hass.locale?.number_format||t.locale?.time_format!==this.hass.locale?.time_format;return o||n||e.has("_historyState")}return!0}_trendEntities(){if(!this.hass||!this._config?.resorts)return[];const e=this._getResorts(this.hass,this._config);return Object.values(e).flatMap(e=>[e.snow_mountain,e.snow_valley,e.new_snow,e.lifts_open_count,e.lifts_open,e.slopes_open_km,e.slopes_open_count,e.slopes_open,e.classical_trails_open,e.skating_trails_open]).filter(Boolean)}_refreshTrendBaseline(){if(!this.hass||!this._config?.show_trend)return void(this._trendBaselineKey=void 0);const e=this._trendEntities();if(0===e.length)return;const t=`${Math.floor(Date.now()/36e5)}|${e.map(e=>`${e}=${this.hass.states[e]?.state}`).join("|")}`;t!==this._trendBaselineKey&&(this._trendBaselineKey=t,this._fetchHistory(e))}async _fetchHistory(e){this._historyState=await async function(e,t,s){if(0===t.length)return{};const i=new Date;i.setHours(i.getHours()-s);try{const s=await e.callWS({type:"history/history_during_period",start_time:i.toISOString(),end_time:i.toISOString(),entity_ids:t,no_attributes:!0}),o={};return Object.entries(s).forEach(([e,t])=>{Array.isArray(t)&&t.length>0&&(o[e]=t[0].s)}),o}catch(e){return console.error(`Error fetching history for ${t.join(", ")}:`,e),{}}}(this.hass,e,24)}_renderTrend(e,t){if(!this._config.show_trend)return W``;const s=this._historyState[e];if(void 0===s||this._isNA(t)||this._isNA(s))return W``;const i=parseFloat(t),o=parseFloat(s);return isNaN(i)||isNaN(o)?W``:i>o?W`<ha-icon class="trend-icon up" icon="mdi:trending-up"></ha-icon>`:i<o?W`<ha-icon class="trend-icon down" icon="mdi:trending-down"></ha-icon>`:W`<ha-icon class="trend-icon same" icon="mdi:trending-neutral"></ha-icon>`}_handleMoreInfo(e){Ne(this,"hass-more-info",{entityId:e})}_handleTabChange(e,t,s){s.stopPropagation(),this._forecastState={...this._forecastState,[e]:{...this._forecastState[e],tab:t,index:0}}}_handleCarouselChange(e,t,s,i){i.stopPropagation();const o=this._forecastState[e]||{tab:"daily",index:0};let n=o.index+("next"===t?1:-1);n<0&&(n=s-1),n>=s&&(n=0),this._forecastState={...this._forecastState,[e]:{...o,index:n}}}_toggleAccordion(e,t,s){s.stopPropagation();const i=this._accordionState[e]||{},o=i[t]??this._config[`${t}_default_open`]??!1;this._accordionState={...this._accordionState,[e]:{...i,[t]:!o}}}_usableForecastImages(e,t,s){if(!t)return[];const i=t.filter(t=>{const s=e.states[t];return void 0!==s&&!("unavailable"===s.state&&s.attributes?.restored)}),o=new Set;return[...i].sort().filter(e=>{const t=e.match(s)?.[1];return void 0===t||!o.has(t)&&(o.add(t),!0)})}_formatForecastDate(e){const t=new Date;if(t.setDate(t.getDate()+e),0===e)return Ae(this.hass,"component.bergfex-card.card.forecast.today");if(1===e)return Ae(this.hass,"component.bergfex-card.card.forecast.tomorrow");{const e=this.hass.locale?.language||this.hass.language||"en";return t.toLocaleDateString(e,{weekday:"short",day:"numeric",month:"short"})}}_renderProgressBar(e,t){const s=Math.min(100,Math.max(0,e/t*100));return W`
      <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width: ${s}%"></div>
      </div>
    `}_isNA(e){return Oe.includes(e?.trim().toLowerCase())}_statusBadge(e,t){if("open"===(e||"").toLowerCase())return{key:"open",variant:"open"};const s=(new Date).toISOString().slice(0,10),i=e=>{const i=t[`${e}_season_start`],o=t[`${e}_season_end`];return Boolean(i&&o&&i<=s&&s<=o)};return i("winter")?{key:"winter_season",variant:"winter-season"}:i("summer")?{key:"summer_season",variant:"summer-season"}:"closed"===(e||"").toLowerCase()?{key:"closed",variant:"closed"}:{key:"unknown",variant:""}}_winterTeaser(e){const t=e.winter_season_start;if(!t)return;const s=(new Date).toISOString().slice(0,10),i=e.winter_season_end;if(t<=s&&(!i||s<=i))return;const o=new Date(`${t}T00:00:00`);if(Number.isNaN(o.getTime()))return;const n=this.hass.locale?.language||this.hass.language||"en",a=new Intl.DateTimeFormat(n,{day:"numeric",month:"short"}).format(o);if(t>s)return Ae(this.hass,"component.bergfex-card.card.status.season_from",{date:a});return(Date.now()-o.getTime())/2630016e3>18?void 0:Ae(this.hass,"component.bergfex-card.card.status.season_last_year",{date:a})}_isOutOfSeason(e){const t=e.status?this.hass.states[e.status]:void 0;return!t||"open"!==t.state.toLowerCase()&&"closed"===this._statusBadge(t.state,t.attributes??{}).variant}_conditionText(e){return this._isNA(e)?Ae(this.hass,"component.bergfex-card.card.status.unknown"):e}_isCrossCountryResort(e){return!!(e.is_cross_country||e.classical_trails_open||e.skating_trails_open||e.classical_condition||e.skating_condition)}render(){if(!this._config)return W``;if(!this.hass||0===this._config.resorts.length)return W`
        <ha-card .header=${this._config.title} tabindex="0">
          <div class="card-content">
            <div class="warning">${Ae(this.hass,"common.errors.no_resorts")}</div>
          </div>
        </ha-card>
      `;let e=Object.entries(this._getResorts(this.hass,this._config));this._config.hide_closed_resorts&&(e=e.filter(([,e])=>!this._isOutOfSeason(e)));const t=this._config.sort_by;return t&&"none"!==t&&e.sort(([,e],[,s])=>{let i,o;switch(t){case"mountain":if(this._isCrossCountryResort(e)||this._isCrossCountryResort(s))break;i=e.snow_mountain?parseFloat(this.hass.states[e.snow_mountain].state):NaN,o=s.snow_mountain?parseFloat(this.hass.states[s.snow_mountain].state):NaN;break;case"valley":if(this._isCrossCountryResort(e)||this._isCrossCountryResort(s))break;i=e.snow_valley?parseFloat(this.hass.states[e.snow_valley].state):NaN,o=s.snow_valley?parseFloat(this.hass.states[s.snow_valley].state):NaN;break;case"new":if(this._isCrossCountryResort(e)||this._isCrossCountryResort(s))break;i=e.new_snow?parseFloat(this.hass.states[e.new_snow].state):NaN,o=s.new_snow?parseFloat(this.hass.states[s.new_snow].state):NaN;break;case"lift":{if(this._isCrossCountryResort(e)||this._isCrossCountryResort(s))break;const t=e=>{const t=e.lifts_open_count??e.lifts_open;return t?parseFloat(this.hass.states[t]?.state??""):NaN};i=t(e),o=t(s);break}case"classical":i=e.classical_trails_open?parseFloat(this.hass.states[e.classical_trails_open].state):NaN,o=s.classical_trails_open?parseFloat(this.hass.states[s.classical_trails_open].state):NaN;break;case"skating":i=e.skating_trails_open?parseFloat(this.hass.states[e.skating_trails_open].state):NaN,o=s.skating_trails_open?parseFloat(this.hass.states[s.skating_trails_open].state):NaN;break;case"update":{const t=Ce(e.last_update?this.hass.states[e.last_update]?.state:void 0)?.getTime(),i=Ce(s.last_update?this.hass.states[s.last_update]?.state:void 0)?.getTime();return void 0===t&&void 0===i?0:void 0===t?1:void 0===i?-1:i-t}}if("number"==typeof i&&"number"==typeof o){const e=isNaN(i),t=isNaN(o);return e&&t?0:e?1:t?-1:o-i}return 0}),W`
      <ha-card .header=${this._config.title} tabindex="0">
        <div class="card-content">
          ${e.map(([e,t])=>{const s=t.status;if(t.problem||!s){const s=t.problem??{reason:"unavailable",subject:t.name??e};return W` <div class="warning">${function(e,t){const s={subject:t.subject};return"wrong_domain"===t.reason&&(s.expected=t.expected,s.actual=t.actual),"not_numeric"===t.reason&&(s.state=t.state),Ae(e,`component.bergfex-card.card.warnings.${t.reason}`,s)}(this.hass,s)}</div> `}const i=this.hass.devices[e],o=t.name||i?.name_by_user||i?.name||"Unknown Resort",n=t.operation_status?this.hass.states[t.operation_status]:void 0,a=t.status?this.hass.states[t.status]:void 0,r=a?.state??"unknown",l=r,c=this._statusBadge(r,a?.attributes??{}),d=this._winterTeaser(a?.attributes??{}),h=Ae(this.hass,`component.bergfex-card.card.status.${c.key}`)||l,p=a?.attributes.link,u=t.snow_valley?this.hass.states[t.snow_valley]:void 0,_=t.snow_mountain?this.hass.states[t.snow_mountain]:void 0,m=t.new_snow?this.hass.states[t.new_snow]:void 0,f=t.lifts_open_count?this.hass.states[t.lifts_open_count]:void 0,g=f||(t.lifts_open?this.hass.states[t.lifts_open]:void 0),v=t.last_update?this.hass.states[t.last_update]:void 0,w=Ce(v?.state),y=t.snow_condition?this.hass.states[t.snow_condition]:void 0,b=t.slope_condition?this.hass.states[t.slope_condition]:void 0,$=t.last_snowfall?this.hass.states[t.last_snowfall]:void 0,k=t.avalanche_warning?this.hass.states[t.avalanche_warning]:void 0,x=t.slopes_open_km?this.hass.states[t.slopes_open_km]:void 0,S=t.slopes_open_count?this.hass.states[t.slopes_open_count]:void 0,A=S||(t.slopes_open?this.hass.states[t.slopes_open]:void 0),N=t.classical_trails_open?this.hass.states[t.classical_trails_open]:void 0,C=t.skating_trails_open?this.hass.states[t.skating_trails_open]:void 0,z=t.classical_condition?this.hass.states[t.classical_condition]:void 0,P=t.skating_condition?this.hass.states[t.skating_condition]:void 0,j=this._isCrossCountryResort(t),E=N?.attributes?.total,T=C?.attributes?.total,O=g?.attributes?.total,M=x?.attributes?.total,R=A?.attributes?.total,D=this._accordionState[e]?.conditions??this._config.conditions_default_open,L=this._accordionState[e]?.forecast??this._config.forecast_default_open;return W`
              <div class="resort" tabindex="0" @click=${()=>this._handleMoreInfo(s)}>
                <div class="resort-header">
                  <span class="resort-name">${o}</span>
                  <div class="resort-status-group">
                    <span
                      class=${ye({"resort-status":!0,[c.variant]:Boolean(c.variant)})}
                      >${h}</span
                    >
                    ${d?W`<span class="season-teaser">${d}</span>`:""}
                  </div>
                </div>

                <div class=${j?"details cross-country-details":"details"}>
                  ${this._config.show_snow&&!j?W`
                          <div
                            class=${ye({"detail-item":!0,"n-a":!_||isNaN(parseFloat(_.state))})}
                            @click=${e=>{e.stopPropagation(),_&&this._handleMoreInfo(_.entity_id)}}
                          >
                            <span class="custom-icon stroke">${ke('<?xml version="1.0" encoding="utf-8"?>\n\x3c!-- License: MIT. Made by Lucide Contributors: https://lucide.dev/ --\x3e\n<svg \n  xmlns="http://www.w3.org/2000/svg"\n  width="24"\n  height="24"\n  viewBox="0 0 24 24"\n  fill="none"\n  stroke="#000000"\n  stroke-width="2"\n  stroke-linecap="round"\n  stroke-linejoin="round"\n>\n  \x3c!-- Mountain --\x3e\n  <path d="M8 3l4 8 5-5 5 15H2L8 3z" />\n  <path d="M4.14 15.08c2.62-1.57 5.24-1.43 7.86.42 2.74 1.94 5.49 2 8.23.19" />\n\n  \x3c!-- Left-pointing arrow further right from first peak --\x3e\n  <g stroke-width="1">\n    <line x1="15" y1="3" x2="10" y2="3" />\n    <polyline points="12,1 10,3 12,5" />\n  </g>\n</svg>')}</span>
                            <div class="detail-item-value">
                              ${_&&!isNaN(parseFloat(_.state))?W`<div class="value-row">
                                      <span
                                        >${ze(_.state,this.hass)}
                                        ${_.attributes.unit_of_measurement??""}</span
                                      >
                                      ${this._renderTrend(_.entity_id,_.state)}
                                    </div>`:W`<span>N/A</span>`}
                              <span class="detail-item-label"
                                >${Ae(this.hass,"component.bergfex-card.card.header.snow_mountain")}
                                ${_?.attributes.elevation?`(${_.attributes.elevation}m)`:""}</span
                              >
                            </div>
                          </div>
                          <div
                            class=${ye({"detail-item":!0,"n-a":!u||isNaN(parseFloat(u.state))})}
                            @click=${e=>{e.stopPropagation(),u&&this._handleMoreInfo(u.entity_id);const t=e.currentTarget;t.classList.add("clicked"),setTimeout(()=>{t.classList.remove("clicked")},500)}}
                          >
                            <span class="custom-icon stroke">${ke('<?xml version="1.0" encoding="utf-8"?>\n\x3c!-- License: MIT. Made by Lucide Contributors: https://lucide.dev/ --\x3e\n<svg \n  xmlns="http://www.w3.org/2000/svg"\n  width="24"\n  height="24"\n  viewBox="0 0 24 24"\n  fill="none"\n  stroke="#000000"\n  stroke-width="2"\n  stroke-linecap="round"\n  stroke-linejoin="round"\n>\n  <path d="M8 3l4 8 5-5 5 15H2L8 3z" />\n  <path d="M4.14 15.08c2.62-1.57 5.24-1.43 7.86.42 2.74 1.94 5.49 2 8.23.19" />\n\n  <g stroke-width="1">\n    <line x1="5" y1="17.5" x2="10" y2="17.5" />\n    <polyline points="8,15.5 5,17.5 8,19.5" />\n  </g>\n</svg>')}</span>
                            <div class="detail-item-value">
                              ${u&&!isNaN(parseFloat(u.state))?W`<div class="value-row">
                                      <span
                                        >${ze(u.state,this.hass)}
                                        ${u.attributes.unit_of_measurement??""}</span
                                      >
                                      ${this._renderTrend(u.entity_id,u.state)}
                                    </div>`:W`<span>N/A</span>`}
                              <span class="detail-item-label"
                                >${Ae(this.hass,"component.bergfex-card.card.header.snow_valley")}
                                ${u?.attributes.elevation?`(${u.attributes.elevation}m)`:""}</span
                              >
                            </div>
                          </div>
                          <div
                            class=${ye({"detail-item":!0,"n-a":!m||isNaN(parseFloat(m.state))})}
                            @click=${e=>{e.stopPropagation(),m&&this._handleMoreInfo(m.entity_id)}}
                          >
                            <ha-icon icon="mdi:weather-snowy-heavy"></ha-icon>
                            <div class="detail-item-value">
                              ${m&&!isNaN(parseFloat(m.state))?W`<div class="value-row">
                                      <span
                                        >${ze(m.state,this.hass)}
                                        ${m.attributes.unit_of_measurement??""}</span
                                      >
                                      ${this._renderTrend(m.entity_id,m.state)}
                                    </div>`:W`<span>N/A</span>`}
                              <span class="detail-item-label"
                                >${Ae(this.hass,"component.bergfex-card.card.header.new_snow")}</span
                              >
                            </div>
                          </div>
                        `:""}
                  ${j&&this._config.show_trails?W`
                          ${N?W`
                                  <div
                                    class=${ye({"detail-item":!0,"n-a":!N||isNaN(parseFloat(N.state))})}
                                    @click=${e=>{e.stopPropagation(),N&&this._handleMoreInfo(N.entity_id)}}
                                  >
                                    <span class="custom-icon fill">${ke(Ee)}</span>
                                    <div class="detail-item-value">
                                      ${N&&!isNaN(parseFloat(N.state))?(()=>{const e=parseFloat(N.state),t=N.attributes.unit_of_measurement??"km",s=E?parseFloat(String(E)):NaN;return isNaN(s)?W`<div class="value-row">
                                                <span>${ze(N.state,this.hass)} ${t}</span>
                                                ${this._renderTrend(N.entity_id,N.state)}
                                              </div>`:W`<div class="value-row">
                                                    <span
                                                      >${ze(e,this.hass)}/${ze(s,this.hass)}
                                                      ${t}</span
                                                    >
                                                    ${this._renderTrend(N.entity_id,N.state)}
                                                  </div>
                                                  ${this._renderProgressBar(e,s)}`})():W`<span>N/A</span>`}
                                      <span class="detail-item-label"
                                        >${Ae(this.hass,"component.bergfex-card.card.header.classical_trails")}</span
                                      >
                                    </div>
                                  </div>
                                `:""}
                          ${C?W`
                                  <div
                                    class=${ye({"detail-item":!0,"n-a":!C||isNaN(parseFloat(C.state))})}
                                    @click=${e=>{e.stopPropagation(),C&&this._handleMoreInfo(C.entity_id)}}
                                  >
                                    <span class="custom-icon fill">${ke(Te)}</span>
                                    <div class="detail-item-value">
                                      ${C&&!isNaN(parseFloat(C.state))?(()=>{const e=parseFloat(C.state),t=C.attributes.unit_of_measurement??"km",s=T?parseFloat(String(T)):NaN;return isNaN(s)?W`<div class="value-row">
                                                <span>${ze(C.state,this.hass)} ${t}</span>
                                                ${this._renderTrend(C.entity_id,C.state)}
                                              </div>`:W`<div class="value-row">
                                                    <span
                                                      >${ze(e,this.hass)}/${ze(s,this.hass)}
                                                      ${t}</span
                                                    >
                                                    ${this._renderTrend(C.entity_id,C.state)}
                                                  </div>
                                                  ${this._renderProgressBar(e,s)}`})():W`<span>N/A</span>`}
                                      <span class="detail-item-label"
                                        >${Ae(this.hass,"component.bergfex-card.card.header.skating_trails")}</span
                                      >
                                    </div>
                                  </div>
                                `:""}
                        `:W`
                          ${this._config.show_lifts_slopes&&g?W`
                                  <div
                                    class=${ye({"detail-item":!0,"n-a":!g||isNaN(parseFloat(g.state))})}
                                    @click=${e=>{e.stopPropagation(),g&&this._handleMoreInfo(g.entity_id)}}
                                  >
                                    <ha-icon icon="mdi:gondola"></ha-icon>
                                    <div class="detail-item-value">
                                      ${g&&!isNaN(parseFloat(g.state))?(()=>{const e=parseFloat(g.state),t=O?parseFloat(String(O)):NaN;return isNaN(t)?W`<div class="value-row">
                                                <span>${ze(g.state,this.hass)}</span>
                                                ${this._renderTrend(g.entity_id,g.state)}
                                              </div>`:W`<div class="value-row">
                                                    <span
                                                      >${ze(e,this.hass)}/${ze(t,this.hass)}</span
                                                    >
                                                    ${this._renderTrend(g.entity_id,g.state)}
                                                  </div>
                                                  ${this._renderProgressBar(e,t)}`})():W`<span>N/A</span>`}
                                      <span class="detail-item-label"
                                        >${Ae(this.hass,"component.bergfex-card.card.lifts_open")}</span
                                      >
                                    </div>
                                  </div>
                                `:""}
                          ${this._config.show_lifts_slopes&&(x||A)?W`
                                  ${x?W`
                                          <div
                                            class=${ye({"detail-item":!0,"n-a":!x||isNaN(parseFloat(x.state))})}
                                            @click=${e=>{e.stopPropagation(),x&&this._handleMoreInfo(x.entity_id)}}
                                          >
                                            <span class="custom-icon stroke">
                                              <ha-icon icon="mdi:slope-downhill"></ha-icon>
                                            </span>
                                            <div class="detail-item-value">
                                              ${x&&!isNaN(parseFloat(x.state))?(()=>{const e=parseFloat(x.state),t=M?parseFloat(String(M)):NaN,s=x.attributes.unit_of_measurement??"km";return isNaN(t)?W`<div class="value-row">
                                                        <span
                                                          >${ze(x.state,this.hass)}
                                                          ${s}</span
                                                        >
                                                        ${this._renderTrend(x.entity_id,x.state)}
                                                      </div>`:W`<div class="value-row">
                                                            <span
                                                              >${ze(e,this.hass)}/${ze(t,this.hass)}
                                                              ${s}</span
                                                            >
                                                            ${this._renderTrend(x.entity_id,x.state)}
                                                          </div>
                                                          ${this._renderProgressBar(e,t)}`})():W`<span>N/A</span>`}
                                              <span class="detail-item-label"
                                                >${Ae(this.hass,"component.bergfex-card.card.header.slopes_info_km")}</span
                                              >
                                            </div>
                                          </div>
                                        `:""}
                                  ${A&&R?W`
                                          <div
                                            class=${ye({"detail-item":!0,"n-a":!A||isNaN(parseFloat(A.state))||isNaN(parseFloat(String(R??NaN)))})}
                                            @click=${e=>{e.stopPropagation(),A&&this._handleMoreInfo(A.entity_id)}}
                                          >
                                            <ha-icon icon="mdi:counter"></ha-icon>
                                            <div class="detail-item-value">
                                              ${A&&!isNaN(parseFloat(A.state))?(()=>{const e=parseFloat(A.state),t=R?parseFloat(String(R)):NaN;return isNaN(t)?W`<div class="value-row">
                                                        <span
                                                          >${ze(A.state,this.hass)}</span
                                                        >
                                                        ${this._renderTrend(A.entity_id,A.state)}
                                                      </div>`:W`<div class="value-row">
                                                            <span
                                                              >${ze(e,this.hass)}/${ze(t,this.hass)}</span
                                                            >
                                                            ${this._renderTrend(A.entity_id,A.state)}
                                                          </div>
                                                          ${this._renderProgressBar(e,t)}`})():W`<span>N/A</span>`}
                                              <span class="detail-item-label"
                                                >${Ae(this.hass,"component.bergfex-card.card.header.slopes_info")}
                                                (${Ae(this.hass,"component.bergfex-card.card.header.slopes_total")})</span
                                              >
                                            </div>
                                          </div>
                                        `:A?W`
                                            <div
                                              class=${ye({"detail-item":!0,"n-a":!A||isNaN(parseFloat(A.state))})}
                                              @click=${e=>{e.stopPropagation(),A&&this._handleMoreInfo(A.entity_id)}}
                                            >
                                              <ha-icon icon="mdi:counter"></ha-icon>
                                              <div class="detail-item-value">
                                                ${A&&!isNaN(parseFloat(A.state))?W`<div class="value-row">
                                                        <span
                                                          >${ze(A.state,this.hass)}</span
                                                        >
                                                        ${this._renderTrend(A.entity_id,A.state)}
                                                      </div>`:W`<span>N/A</span>`}
                                                <span class="detail-item-label"
                                                  >${Ae(this.hass,"component.bergfex-card.card.header.slopes_info")}</span
                                                >
                                              </div>
                                            </div>
                                          `:""}
                                `:""}
                        `}
                </div>

                ${this._config.show_conditions&&(y||b||k||$||n||z||P)?W`
                        <div class="accordion-container">
                          <div
                            class="accordion-header"
                            @click=${t=>this._toggleAccordion(e,"conditions",t)}
                          >
                            <span>${Ae(this.hass,"component.bergfex-card.card.accordion.conditions")}</span>
                            <ha-icon icon=${D?"mdi:chevron-up":"mdi:chevron-down"}></ha-icon>
                          </div>
                          ${D?W`
                                  <div class="accordion-content details">
                                    ${this._config.show_conditions&&(y||b)&&!j?W`
                                            ${y?W`
                                                    <div
                                                      class=${ye({"detail-item":!0,"n-a":this._isNA(y.state)})}
                                                      @click=${e=>{e.stopPropagation(),y&&this._handleMoreInfo(y.entity_id)}}
                                                    >
                                                      <ha-icon icon="mdi:weather-snowy"></ha-icon>
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(y.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${Ae(this.hass,"component.bergfex-card.card.header.snow_condition")}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `:""}
                                            ${b?W`
                                                    <div
                                                      class=${ye({"detail-item":!0,"n-a":this._isNA(b.state)})}
                                                      @click=${e=>{e.stopPropagation(),b&&this._handleMoreInfo(b.entity_id)}}
                                                    >
                                                      <ha-icon icon="mdi:ski"></ha-icon>
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(b.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${Ae(this.hass,"component.bergfex-card.card.header.slope_condition")}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `:""}
                                          `:""}
                                    ${this._config.show_conditions&&k&&!j?W`
                                            <div
                                              class=${ye({"detail-item":!0,"n-a":this._isNA(k.state)})}
                                              @click=${e=>{e.stopPropagation(),k&&this._handleMoreInfo(k.entity_id)}}
                                            >
                                              <ha-icon icon="mdi:alert"></ha-icon>
                                              <div class="detail-item-value">
                                                <span>${this._conditionText(k.state)}</span>
                                                <span class="detail-item-label"
                                                  >${Ae(this.hass,"component.bergfex-card.card.header.avalanche_warning")}</span
                                                >
                                              </div>
                                            </div>
                                          `:""}
                                    ${this._config.show_conditions&&(z||P)?W`
                                            ${z?W`
                                                    <div
                                                      class=${ye({"detail-item":!0,"n-a":this._isNA(z.state)})}
                                                      @click=${e=>{e.stopPropagation(),z&&this._handleMoreInfo(z.entity_id)}}
                                                    >
                                                      <span class="custom-icon fill"
                                                        >${ke(Ee)}</span
                                                      >
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(z.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${Ae(this.hass,"component.bergfex-card.card.header.classical_condition")}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `:""}
                                            ${P?W`
                                                    <div
                                                      class=${ye({"detail-item":!0,"n-a":this._isNA(P.state)})}
                                                      @click=${e=>{e.stopPropagation(),P&&this._handleMoreInfo(P.entity_id)}}
                                                    >
                                                      <span class="custom-icon fill"
                                                        >${ke(Te)}</span
                                                      >
                                                      <div class="detail-item-value">
                                                        <span>${this._conditionText(P.state)}</span>
                                                        <span class="detail-item-label"
                                                          >${Ae(this.hass,"component.bergfex-card.card.header.skating_condition")}</span
                                                        >
                                                      </div>
                                                    </div>
                                                  `:""}
                                          `:""}
                                    ${$?W`
                                            <div
                                              class=${ye({"detail-item":!0,"n-a":this._isNA($.state)})}
                                              @click=${e=>{e.stopPropagation(),this._handleMoreInfo($.entity_id)}}
                                            >
                                              <ha-icon icon="mdi:calendar-clock"></ha-icon>
                                              <div class="detail-item-value">
                                                <span>${this._conditionText($.state)}</span>
                                                <span class="detail-item-label"
                                                  >${Ae(this.hass,"component.bergfex-card.card.header.last_snowfall")}</span
                                                >
                                              </div>
                                            </div>
                                          `:""}
                                    ${this._config.show_conditions&&n?W`
                                            <div
                                              class=${ye({"detail-item":!0,"n-a":this._isNA(n.state)})}
                                              @click=${e=>{e.stopPropagation(),n&&this._handleMoreInfo(n.entity_id)}}
                                            >
                                              <ha-icon icon="mdi:information-outline"></ha-icon>
                                              <div class="detail-item-value">
                                                <span>${this._conditionText(n.state)}</span>
                                                <span class="detail-item-label"
                                                  >${Ae(this.hass,"component.bergfex-card.card.header.operation_status")}</span
                                                >
                                              </div>
                                            </div>
                                          `:""}
                                  </div>
                                `:""}
                        </div>
                      `:""}
                ${(()=>{if(!this._config.show_forecast)return"";const s=t.forecast_days&&t.forecast_days.length>0&&t.forecast_days.some(e=>{const t=this.hass.states[e];return t&&t.attributes.entity_picture}),i=t.forecast_summaries&&t.forecast_summaries.length>0&&t.forecast_summaries.some(e=>{const t=this.hass.states[e];return t&&t.attributes.entity_picture});return s||i?W`
                    <div class="accordion-container">
                      <div
                        class="accordion-header"
                        @click=${t=>this._toggleAccordion(e,"forecast",t)}
                      >
                        <span>${Ae(this.hass,"component.bergfex-card.card.accordion.forecast")}</span>
                        <ha-icon icon=${L?"mdi:chevron-up":"mdi:chevron-down"}></ha-icon>
                      </div>
                      ${L?W`
                              <div class="forecast-container">
                                <div class="forecast-tabs">
                                  ${s?W`
                                          <div
                                            class="forecast-tab ${this._forecastState[e]&&"daily"!==this._forecastState[e].tab?"":"active"}"
                                            @click=${t=>this._handleTabChange(e,"daily",t)}
                                          >
                                            ${Ae(this.hass,"component.bergfex-card.card.forecast.daily")}
                                          </div>
                                        `:""}
                                  ${i?W`
                                          <div
                                            class="forecast-tab ${"summary"===this._forecastState[e]?.tab?"active":""}"
                                            @click=${t=>this._handleTabChange(e,"summary",t)}
                                          >
                                            ${Ae(this.hass,"component.bergfex-card.card.forecast.summary")}
                                          </div>
                                        `:""}
                                </div>

                                <div class="forecast-carousel">
                                  ${(()=>{const s=this._forecastState[e]?.tab||"daily",i="daily"===s?t.forecast_days:t.forecast_summaries,o=this._forecastState[e]?.index||0;if(!i||0===i.length)return W``;const n=i[o],a=this.hass.states[n],r=a?.attributes.entity_picture;let l;if("daily"===s){const e=n.match(/day_(\d+)/),t=e?parseInt(e[1],10):o;l=this._formatForecastDate(t)}else{const e=n.match(/summary_image_(\d+)h/),t=e?e[1]:"";l=Ae(this.hass,"component.bergfex-card.card.forecast.hour",{hours:t})}return W`
                                      <div class="forecast-image-container">
                                        ${r?W`<img
                                                src="${r}"
                                                class="forecast-image"
                                                alt="${l}"
                                                @click=${e=>{e.stopPropagation(),this._handleMoreInfo(n)}}
                                                style="cursor: pointer;"
                                              />`:W`<span>Image not available</span>`}
                                      </div>
                                      <div class="carousel-controls">
                                        <button
                                          class="carousel-btn"
                                          @click=${t=>this._handleCarouselChange(e,"prev",i.length,t)}
                                          ?disabled=${i.length<=1}
                                        >
                                          <ha-icon icon="mdi:chevron-left"></ha-icon>
                                        </button>
                                        <span class="carousel-label">${l}</span>
                                        <button
                                          class="carousel-btn"
                                          @click=${t=>this._handleCarouselChange(e,"next",i.length,t)}
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
                            title=${Ae(this.hass,"component.bergfex-card.card.link_title",{resortName:o})}
                            @click=${e=>e.stopPropagation()}
                          >
                            <ha-icon icon="mdi:link-variant"></ha-icon>
                          </a>
                        `:W`<div></div>`}
                  ${this._config.show_last_updated&&v&&w?W`
                          <div
                            class="last-updated"
                            @click=${e=>{e.stopPropagation(),v&&this._handleMoreInfo(v.entity_id)}}
                          >
                            <ha-icon icon="mdi:clock-outline"></ha-icon>
                            <span>${Pe(w,this.hass)}</span>
                          </div>
                        `:""}
                </div>
              </div>
            `})}
        </div>
      </ha-card>
    `}static{this.styles=r`
    ${a(je)}
  `}}e([pe({attribute:!1})],De.prototype,"hass",void 0),e([
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function(e){return(t,s,i)=>((e,t,s)=>(s.configurable=!0,s.enumerable=!0,Reflect.decorate&&"object"!=typeof t&&Object.defineProperty(e,t,s),s))(t,s,{get(){return(t=>t.renderRoot?.querySelector(e)??null)(this)}})}("ha-card")],De.prototype,"_card",void 0),e([ue()],De.prototype,"_config",void 0),e([ue()],De.prototype,"_forecastState",void 0),e([ue()],De.prototype,"_accordionState",void 0),e([ue()],De.prototype,"_historyState",void 0),customElements.get(Me)?console.warn(`${Me}: another copy of this card is already loaded, so this one stays inactive. The card now ships with the Bergfex integration - uninstall "Bergfex Card" from HACS and reload your browser.`):customElements.define(Me,De),"undefined"!=typeof window&&(window.customCards=window.customCards||[],window.customCards.some(e=>e.type===Me)||window.customCards.push({type:Me,name:"Bergfex Card",description:"A Lovelace card to display ski resort conditions from Bergfex.",documentationURL:"https://github.com/timmaurice/bergfex",getEntitySuggestion:(e,t)=>{const s=e.entities[t];return"bergfex"===s?.platform&&s.device_id?{config:{type:`custom:${Me}`,resorts:[s.device_id]}}:null}}));const Le=r`.card-config{display:flex;flex-direction:column;gap:12px}.group{border:1px solid var(--divider-color);border-radius:var(--ha-card-border-radius, 12px);margin-top:0;padding:16px}.group-header{color:var(--primary-text-color);font-size:16px;font-weight:500;margin-bottom:12px}ha-form{display:block}`;function Fe(e){return"string"==typeof e?e:e.device}const Ue=[{name:"title",selector:{text:{}}},{name:"resorts",selector:{device:{multiple:!0,integration:"bergfex"}}},{type:"expandable",title:"groups.display",schema:[{name:"show_conditions",selector:{boolean:{}}},{name:"conditions_default_open",selector:{boolean:{}}},{name:"show_trend",selector:{boolean:{}}},{name:"show_link",selector:{boolean:{}}},{name:"show_last_updated",selector:{boolean:{}}},{name:"hide_closed_resorts",selector:{boolean:{}}},{name:"sort_by",selector:{select:{mode:"dropdown"}}}]},{type:"expandable",title:"groups.cross_country_only",schema:[{name:"show_trails",selector:{boolean:{}}}]},{type:"expandable",title:"groups.ski_only",schema:[{name:"show_snow",selector:{boolean:{}}},{name:"show_lifts_slopes",selector:{boolean:{}}},{name:"show_forecast",selector:{boolean:{}}},{name:"forecast_default_open",selector:{boolean:{}}}]}],Be="bergfex-card-editor";class Ie extends le{setConfig(e){this._config=e}_helper(e){const t=`component.bergfex-card.editor.${e}_helper`,s=Ae(this.hass,t);return s===t?void 0:s}_valueChanged(e){if(!this.hass||!this._config)return;const t={...e.detail.value};if(Array.isArray(t.resorts)){const e=new Map;for(const t of this._config.resorts??[])t&&"object"==typeof t&&t.name&&e.set(t.device,t.name);t.resorts=t.resorts.filter(e=>Boolean(e)&&Boolean(Fe(e))).map(t=>{const s=Fe(t),i=e.get(s);return i?{device:s,name:i}:s})}Ne(this,"config-changed",{config:me({...this._config,...t})})}render(){if(!this.hass||!this._config)return W``;const e=[{value:"mountain",label:Ae(this.hass,"component.bergfex-card.editor.sort_by_options.mountain")},{value:"valley",label:Ae(this.hass,"component.bergfex-card.editor.sort_by_options.valley")},{value:"new",label:Ae(this.hass,"component.bergfex-card.editor.sort_by_options.new")},{value:"lift",label:Ae(this.hass,"component.bergfex-card.editor.sort_by_options.lift")},{value:"classical",label:Ae(this.hass,"component.bergfex-card.editor.sort_by_options.classical")},{value:"skating",label:Ae(this.hass,"component.bergfex-card.editor.sort_by_options.skating")},{value:"update",label:Ae(this.hass,"component.bergfex-card.editor.sort_by_options.update")}],t=(t=>t.reduce((t,s)=>{const i={...s};if("expandable"===i.type&&Array.isArray(i.schema)){const s=i.schema.map(e=>({...e}));return"groups.display"===i.title&&s.forEach(t=>{"sort_by"===t.name&&(t.selector={select:{mode:"dropdown",clearable:!0,options:e}})}),i.title="string"==typeof i.title?Ae(this.hass,`component.bergfex-card.editor.${i.title}`):i.title,i.schema=s,t.push(i),t}return"resorts"===i.name&&(i.selector={device:{multiple:!0,integration:"bergfex"}}),t.push(i),t},[]))(Ue),s={..._e,...this._config,resorts:(this._config.resorts??[]).filter(Boolean).map(Fe)};return W`
      <ha-card>
        <div class="card-content card-config">
          <ha-form
            .schema=${t}
            .hass=${this.hass}
            .data=${s}
            .computeLabel=${e=>Ae(this.hass,`component.bergfex-card.editor.${e.name}`)}
            .computeHelper=${e=>this._helper(e.name)}
            @value-changed=${this._valueChanged}
          ></ha-form>
        </div>
      </ha-card>
    `}static{this.styles=r`
    ${a(Le)}
  `}}e([pe({attribute:!1})],Ie.prototype,"hass",void 0),e([ue()],Ie.prototype,"_config",void 0),customElements.get(Be)||customElements.define(Be,Ie);var He=Object.freeze({__proto__:null,BergfexCardEditor:Ie});export{De as BergfexCard};
