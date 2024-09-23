"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
var __export = (target, all) => {
  for (var name3 in all)
    __defProp(target, name3, { get: all[name3], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// ../../node_modules/jsonify/lib/parse.js
var require_parse = __commonJS({
  "../../node_modules/jsonify/lib/parse.js"(exports2, module2) {
    "use strict";
    var at;
    var ch;
    var escapee = {
      '"': '"',
      "\\": "\\",
      "/": "/",
      b: "\b",
      f: "\f",
      n: "\n",
      r: "\r",
      t: "	"
    };
    var text;
    function error2(m) {
      throw {
        name: "SyntaxError",
        message: m,
        at,
        text
      };
    }
    function next(c) {
      if (c && c !== ch) {
        error2("Expected '" + c + "' instead of '" + ch + "'");
      }
      ch = text.charAt(at);
      at += 1;
      return ch;
    }
    function number() {
      var num;
      var str2 = "";
      if (ch === "-") {
        str2 = "-";
        next("-");
      }
      while (ch >= "0" && ch <= "9") {
        str2 += ch;
        next();
      }
      if (ch === ".") {
        str2 += ".";
        while (next() && ch >= "0" && ch <= "9") {
          str2 += ch;
        }
      }
      if (ch === "e" || ch === "E") {
        str2 += ch;
        next();
        if (ch === "-" || ch === "+") {
          str2 += ch;
          next();
        }
        while (ch >= "0" && ch <= "9") {
          str2 += ch;
          next();
        }
      }
      num = Number(str2);
      if (!isFinite(num)) {
        error2("Bad number");
      }
      return num;
    }
    function string() {
      var hex;
      var i;
      var str2 = "";
      var uffff;
      if (ch === '"') {
        while (next()) {
          if (ch === '"') {
            next();
            return str2;
          } else if (ch === "\\") {
            next();
            if (ch === "u") {
              uffff = 0;
              for (i = 0; i < 4; i += 1) {
                hex = parseInt(next(), 16);
                if (!isFinite(hex)) {
                  break;
                }
                uffff = uffff * 16 + hex;
              }
              str2 += String.fromCharCode(uffff);
            } else if (typeof escapee[ch] === "string") {
              str2 += escapee[ch];
            } else {
              break;
            }
          } else {
            str2 += ch;
          }
        }
      }
      error2("Bad string");
    }
    function white() {
      while (ch && ch <= " ") {
        next();
      }
    }
    function word() {
      switch (ch) {
        case "t":
          next("t");
          next("r");
          next("u");
          next("e");
          return true;
        case "f":
          next("f");
          next("a");
          next("l");
          next("s");
          next("e");
          return false;
        case "n":
          next("n");
          next("u");
          next("l");
          next("l");
          return null;
        default:
          error2("Unexpected '" + ch + "'");
      }
    }
    function array() {
      var arr = [];
      if (ch === "[") {
        next("[");
        white();
        if (ch === "]") {
          next("]");
          return arr;
        }
        while (ch) {
          arr.push(value());
          white();
          if (ch === "]") {
            next("]");
            return arr;
          }
          next(",");
          white();
        }
      }
      error2("Bad array");
    }
    function object() {
      var key;
      var obj = {};
      if (ch === "{") {
        next("{");
        white();
        if (ch === "}") {
          next("}");
          return obj;
        }
        while (ch) {
          key = string();
          white();
          next(":");
          if (Object.prototype.hasOwnProperty.call(obj, key)) {
            error2('Duplicate key "' + key + '"');
          }
          obj[key] = value();
          white();
          if (ch === "}") {
            next("}");
            return obj;
          }
          next(",");
          white();
        }
      }
      error2("Bad object");
    }
    function value() {
      white();
      switch (ch) {
        case "{":
          return object();
        case "[":
          return array();
        case '"':
          return string();
        case "-":
          return number();
        default:
          return ch >= "0" && ch <= "9" ? number() : word();
      }
    }
    module2.exports = function(source, reviver) {
      var result;
      text = source;
      at = 0;
      ch = " ";
      result = value();
      white();
      if (ch) {
        error2("Syntax error");
      }
      return typeof reviver === "function" ? function walk(holder, key) {
        var k;
        var v;
        var val = holder[key];
        if (val && typeof val === "object") {
          for (k in value) {
            if (Object.prototype.hasOwnProperty.call(val, k)) {
              v = walk(val, k);
              if (typeof v === "undefined") {
                delete val[k];
              } else {
                val[k] = v;
              }
            }
          }
        }
        return reviver.call(holder, key, val);
      }({ "": result }, "") : result;
    };
  }
});

// ../../node_modules/jsonify/lib/stringify.js
var require_stringify = __commonJS({
  "../../node_modules/jsonify/lib/stringify.js"(exports2, module2) {
    "use strict";
    var escapable = /[\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g;
    var gap;
    var indent;
    var meta = {
      // table of character substitutions
      "\b": "\\b",
      "	": "\\t",
      "\n": "\\n",
      "\f": "\\f",
      "\r": "\\r",
      '"': '\\"',
      "\\": "\\\\"
    };
    var rep;
    function quote(string) {
      escapable.lastIndex = 0;
      return escapable.test(string) ? '"' + string.replace(escapable, function(a) {
        var c = meta[a];
        return typeof c === "string" ? c : "\\u" + ("0000" + a.charCodeAt(0).toString(16)).slice(-4);
      }) + '"' : '"' + string + '"';
    }
    function str2(key, holder) {
      var i;
      var k;
      var v;
      var length;
      var mind = gap;
      var partial;
      var value = holder[key];
      if (value && typeof value === "object" && typeof value.toJSON === "function") {
        value = value.toJSON(key);
      }
      if (typeof rep === "function") {
        value = rep.call(holder, key, value);
      }
      switch (typeof value) {
        case "string":
          return quote(value);
        case "number":
          return isFinite(value) ? String(value) : "null";
        case "boolean":
        case "null":
          return String(value);
        case "object":
          if (!value) {
            return "null";
          }
          gap += indent;
          partial = [];
          if (Object.prototype.toString.apply(value) === "[object Array]") {
            length = value.length;
            for (i = 0; i < length; i += 1) {
              partial[i] = str2(i, value) || "null";
            }
            v = partial.length === 0 ? "[]" : gap ? "[\n" + gap + partial.join(",\n" + gap) + "\n" + mind + "]" : "[" + partial.join(",") + "]";
            gap = mind;
            return v;
          }
          if (rep && typeof rep === "object") {
            length = rep.length;
            for (i = 0; i < length; i += 1) {
              k = rep[i];
              if (typeof k === "string") {
                v = str2(k, value);
                if (v) {
                  partial.push(quote(k) + (gap ? ": " : ":") + v);
                }
              }
            }
          } else {
            for (k in value) {
              if (Object.prototype.hasOwnProperty.call(value, k)) {
                v = str2(k, value);
                if (v) {
                  partial.push(quote(k) + (gap ? ": " : ":") + v);
                }
              }
            }
          }
          v = partial.length === 0 ? "{}" : gap ? "{\n" + gap + partial.join(",\n" + gap) + "\n" + mind + "}" : "{" + partial.join(",") + "}";
          gap = mind;
          return v;
        default:
      }
    }
    module2.exports = function(value, replacer, space) {
      var i;
      gap = "";
      indent = "";
      if (typeof space === "number") {
        for (i = 0; i < space; i += 1) {
          indent += " ";
        }
      } else if (typeof space === "string") {
        indent = space;
      }
      rep = replacer;
      if (replacer && typeof replacer !== "function" && (typeof replacer !== "object" || typeof replacer.length !== "number")) {
        throw new Error("JSON.stringify");
      }
      return str2("", { "": value });
    };
  }
});

// ../../node_modules/jsonify/index.js
var require_jsonify = __commonJS({
  "../../node_modules/jsonify/index.js"(exports2) {
    "use strict";
    exports2.parse = require_parse();
    exports2.stringify = require_stringify();
  }
});

// ../../node_modules/isarray/index.js
var require_isarray = __commonJS({
  "../../node_modules/isarray/index.js"(exports2, module2) {
    var toString = {}.toString;
    module2.exports = Array.isArray || function(arr) {
      return toString.call(arr) == "[object Array]";
    };
  }
});

// ../../node_modules/object-keys/isArguments.js
var require_isArguments = __commonJS({
  "../../node_modules/object-keys/isArguments.js"(exports2, module2) {
    "use strict";
    var toStr = Object.prototype.toString;
    module2.exports = function isArguments(value) {
      var str2 = toStr.call(value);
      var isArgs = str2 === "[object Arguments]";
      if (!isArgs) {
        isArgs = str2 !== "[object Array]" && value !== null && typeof value === "object" && typeof value.length === "number" && value.length >= 0 && toStr.call(value.callee) === "[object Function]";
      }
      return isArgs;
    };
  }
});

// ../../node_modules/object-keys/implementation.js
var require_implementation = __commonJS({
  "../../node_modules/object-keys/implementation.js"(exports2, module2) {
    "use strict";
    var keysShim;
    if (!Object.keys) {
      has = Object.prototype.hasOwnProperty;
      toStr = Object.prototype.toString;
      isArgs = require_isArguments();
      isEnumerable = Object.prototype.propertyIsEnumerable;
      hasDontEnumBug = !isEnumerable.call({ toString: null }, "toString");
      hasProtoEnumBug = isEnumerable.call(function() {
      }, "prototype");
      dontEnums = [
        "toString",
        "toLocaleString",
        "valueOf",
        "hasOwnProperty",
        "isPrototypeOf",
        "propertyIsEnumerable",
        "constructor"
      ];
      equalsConstructorPrototype = function(o) {
        var ctor = o.constructor;
        return ctor && ctor.prototype === o;
      };
      excludedKeys = {
        $applicationCache: true,
        $console: true,
        $external: true,
        $frame: true,
        $frameElement: true,
        $frames: true,
        $innerHeight: true,
        $innerWidth: true,
        $onmozfullscreenchange: true,
        $onmozfullscreenerror: true,
        $outerHeight: true,
        $outerWidth: true,
        $pageXOffset: true,
        $pageYOffset: true,
        $parent: true,
        $scrollLeft: true,
        $scrollTop: true,
        $scrollX: true,
        $scrollY: true,
        $self: true,
        $webkitIndexedDB: true,
        $webkitStorageInfo: true,
        $window: true
      };
      hasAutomationEqualityBug = function() {
        if (typeof window === "undefined") {
          return false;
        }
        for (var k in window) {
          try {
            if (!excludedKeys["$" + k] && has.call(window, k) && window[k] !== null && typeof window[k] === "object") {
              try {
                equalsConstructorPrototype(window[k]);
              } catch (e) {
                return true;
              }
            }
          } catch (e) {
            return true;
          }
        }
        return false;
      }();
      equalsConstructorPrototypeIfNotBuggy = function(o) {
        if (typeof window === "undefined" || !hasAutomationEqualityBug) {
          return equalsConstructorPrototype(o);
        }
        try {
          return equalsConstructorPrototype(o);
        } catch (e) {
          return false;
        }
      };
      keysShim = function keys(object) {
        var isObject = object !== null && typeof object === "object";
        var isFunction = toStr.call(object) === "[object Function]";
        var isArguments = isArgs(object);
        var isString = isObject && toStr.call(object) === "[object String]";
        var theKeys = [];
        if (!isObject && !isFunction && !isArguments) {
          throw new TypeError("Object.keys called on a non-object");
        }
        var skipProto = hasProtoEnumBug && isFunction;
        if (isString && object.length > 0 && !has.call(object, 0)) {
          for (var i = 0; i < object.length; ++i) {
            theKeys.push(String(i));
          }
        }
        if (isArguments && object.length > 0) {
          for (var j = 0; j < object.length; ++j) {
            theKeys.push(String(j));
          }
        } else {
          for (var name3 in object) {
            if (!(skipProto && name3 === "prototype") && has.call(object, name3)) {
              theKeys.push(String(name3));
            }
          }
        }
        if (hasDontEnumBug) {
          var skipConstructor = equalsConstructorPrototypeIfNotBuggy(object);
          for (var k = 0; k < dontEnums.length; ++k) {
            if (!(skipConstructor && dontEnums[k] === "constructor") && has.call(object, dontEnums[k])) {
              theKeys.push(dontEnums[k]);
            }
          }
        }
        return theKeys;
      };
    }
    var has;
    var toStr;
    var isArgs;
    var isEnumerable;
    var hasDontEnumBug;
    var hasProtoEnumBug;
    var dontEnums;
    var equalsConstructorPrototype;
    var excludedKeys;
    var hasAutomationEqualityBug;
    var equalsConstructorPrototypeIfNotBuggy;
    module2.exports = keysShim;
  }
});

// ../../node_modules/object-keys/index.js
var require_object_keys = __commonJS({
  "../../node_modules/object-keys/index.js"(exports2, module2) {
    "use strict";
    var slice = Array.prototype.slice;
    var isArgs = require_isArguments();
    var origKeys = Object.keys;
    var keysShim = origKeys ? function keys(o) {
      return origKeys(o);
    } : require_implementation();
    var originalKeys = Object.keys;
    keysShim.shim = function shimObjectKeys() {
      if (Object.keys) {
        var keysWorksWithArguments = function() {
          var args = Object.keys(arguments);
          return args && args.length === arguments.length;
        }(1, 2);
        if (!keysWorksWithArguments) {
          Object.keys = function keys(object) {
            if (isArgs(object)) {
              return originalKeys(slice.call(object));
            }
            return originalKeys(object);
          };
        }
      } else {
        Object.keys = keysShim;
      }
      return Object.keys || keysShim;
    };
    module2.exports = keysShim;
  }
});

// ../../node_modules/function-bind/implementation.js
var require_implementation2 = __commonJS({
  "../../node_modules/function-bind/implementation.js"(exports2, module2) {
    "use strict";
    var ERROR_MESSAGE = "Function.prototype.bind called on incompatible ";
    var toStr = Object.prototype.toString;
    var max = Math.max;
    var funcType = "[object Function]";
    var concatty = function concatty2(a, b) {
      var arr = [];
      for (var i = 0; i < a.length; i += 1) {
        arr[i] = a[i];
      }
      for (var j = 0; j < b.length; j += 1) {
        arr[j + a.length] = b[j];
      }
      return arr;
    };
    var slicy = function slicy2(arrLike, offset) {
      var arr = [];
      for (var i = offset || 0, j = 0; i < arrLike.length; i += 1, j += 1) {
        arr[j] = arrLike[i];
      }
      return arr;
    };
    var joiny = function(arr, joiner) {
      var str2 = "";
      for (var i = 0; i < arr.length; i += 1) {
        str2 += arr[i];
        if (i + 1 < arr.length) {
          str2 += joiner;
        }
      }
      return str2;
    };
    module2.exports = function bind(that) {
      var target = this;
      if (typeof target !== "function" || toStr.apply(target) !== funcType) {
        throw new TypeError(ERROR_MESSAGE + target);
      }
      var args = slicy(arguments, 1);
      var bound;
      var binder = function() {
        if (this instanceof bound) {
          var result = target.apply(
            this,
            concatty(args, arguments)
          );
          if (Object(result) === result) {
            return result;
          }
          return this;
        }
        return target.apply(
          that,
          concatty(args, arguments)
        );
      };
      var boundLength = max(0, target.length - args.length);
      var boundArgs = [];
      for (var i = 0; i < boundLength; i++) {
        boundArgs[i] = "$" + i;
      }
      bound = Function("binder", "return function (" + joiny(boundArgs, ",") + "){ return binder.apply(this,arguments); }")(binder);
      if (target.prototype) {
        var Empty = function Empty2() {
        };
        Empty.prototype = target.prototype;
        bound.prototype = new Empty();
        Empty.prototype = null;
      }
      return bound;
    };
  }
});

// ../../node_modules/function-bind/index.js
var require_function_bind = __commonJS({
  "../../node_modules/function-bind/index.js"(exports2, module2) {
    "use strict";
    var implementation = require_implementation2();
    module2.exports = Function.prototype.bind || implementation;
  }
});

// ../../node_modules/has-symbols/shams.js
var require_shams = __commonJS({
  "../../node_modules/has-symbols/shams.js"(exports2, module2) {
    "use strict";
    module2.exports = function hasSymbols() {
      if (typeof Symbol !== "function" || typeof Object.getOwnPropertySymbols !== "function") {
        return false;
      }
      if (typeof Symbol.iterator === "symbol") {
        return true;
      }
      var obj = {};
      var sym = Symbol("test");
      var symObj = Object(sym);
      if (typeof sym === "string") {
        return false;
      }
      if (Object.prototype.toString.call(sym) !== "[object Symbol]") {
        return false;
      }
      if (Object.prototype.toString.call(symObj) !== "[object Symbol]") {
        return false;
      }
      var symVal = 42;
      obj[sym] = symVal;
      for (sym in obj) {
        return false;
      }
      if (typeof Object.keys === "function" && Object.keys(obj).length !== 0) {
        return false;
      }
      if (typeof Object.getOwnPropertyNames === "function" && Object.getOwnPropertyNames(obj).length !== 0) {
        return false;
      }
      var syms = Object.getOwnPropertySymbols(obj);
      if (syms.length !== 1 || syms[0] !== sym) {
        return false;
      }
      if (!Object.prototype.propertyIsEnumerable.call(obj, sym)) {
        return false;
      }
      if (typeof Object.getOwnPropertyDescriptor === "function") {
        var descriptor = Object.getOwnPropertyDescriptor(obj, sym);
        if (descriptor.value !== symVal || descriptor.enumerable !== true) {
          return false;
        }
      }
      return true;
    };
  }
});

// ../../node_modules/has-symbols/index.js
var require_has_symbols = __commonJS({
  "../../node_modules/has-symbols/index.js"(exports2, module2) {
    "use strict";
    var origSymbol = typeof Symbol !== "undefined" && Symbol;
    var hasSymbolSham = require_shams();
    module2.exports = function hasNativeSymbols() {
      if (typeof origSymbol !== "function") {
        return false;
      }
      if (typeof Symbol !== "function") {
        return false;
      }
      if (typeof origSymbol("foo") !== "symbol") {
        return false;
      }
      if (typeof Symbol("bar") !== "symbol") {
        return false;
      }
      return hasSymbolSham();
    };
  }
});

// ../../node_modules/has-proto/index.js
var require_has_proto = __commonJS({
  "../../node_modules/has-proto/index.js"(exports2, module2) {
    "use strict";
    var test = {
      foo: {}
    };
    var $Object = Object;
    module2.exports = function hasProto() {
      return { __proto__: test }.foo === test.foo && !({ __proto__: null } instanceof $Object);
    };
  }
});

// ../../node_modules/hasown/index.js
var require_hasown = __commonJS({
  "../../node_modules/hasown/index.js"(exports2, module2) {
    "use strict";
    var call = Function.prototype.call;
    var $hasOwn = Object.prototype.hasOwnProperty;
    var bind = require_function_bind();
    module2.exports = bind.call(call, $hasOwn);
  }
});

// ../../node_modules/get-intrinsic/index.js
var require_get_intrinsic = __commonJS({
  "../../node_modules/get-intrinsic/index.js"(exports2, module2) {
    "use strict";
    var undefined2;
    var $SyntaxError = SyntaxError;
    var $Function = Function;
    var $TypeError = TypeError;
    var getEvalledConstructor = function(expressionSyntax) {
      try {
        return $Function('"use strict"; return (' + expressionSyntax + ").constructor;")();
      } catch (e) {
      }
    };
    var $gOPD = Object.getOwnPropertyDescriptor;
    if ($gOPD) {
      try {
        $gOPD({}, "");
      } catch (e) {
        $gOPD = null;
      }
    }
    var throwTypeError = function() {
      throw new $TypeError();
    };
    var ThrowTypeError = $gOPD ? function() {
      try {
        arguments.callee;
        return throwTypeError;
      } catch (calleeThrows) {
        try {
          return $gOPD(arguments, "callee").get;
        } catch (gOPDthrows) {
          return throwTypeError;
        }
      }
    }() : throwTypeError;
    var hasSymbols = require_has_symbols()();
    var hasProto = require_has_proto()();
    var getProto = Object.getPrototypeOf || (hasProto ? function(x) {
      return x.__proto__;
    } : null);
    var needsEval = {};
    var TypedArray = typeof Uint8Array === "undefined" || !getProto ? undefined2 : getProto(Uint8Array);
    var INTRINSICS = {
      "%AggregateError%": typeof AggregateError === "undefined" ? undefined2 : AggregateError,
      "%Array%": Array,
      "%ArrayBuffer%": typeof ArrayBuffer === "undefined" ? undefined2 : ArrayBuffer,
      "%ArrayIteratorPrototype%": hasSymbols && getProto ? getProto([][Symbol.iterator]()) : undefined2,
      "%AsyncFromSyncIteratorPrototype%": undefined2,
      "%AsyncFunction%": needsEval,
      "%AsyncGenerator%": needsEval,
      "%AsyncGeneratorFunction%": needsEval,
      "%AsyncIteratorPrototype%": needsEval,
      "%Atomics%": typeof Atomics === "undefined" ? undefined2 : Atomics,
      "%BigInt%": typeof BigInt === "undefined" ? undefined2 : BigInt,
      "%BigInt64Array%": typeof BigInt64Array === "undefined" ? undefined2 : BigInt64Array,
      "%BigUint64Array%": typeof BigUint64Array === "undefined" ? undefined2 : BigUint64Array,
      "%Boolean%": Boolean,
      "%DataView%": typeof DataView === "undefined" ? undefined2 : DataView,
      "%Date%": Date,
      "%decodeURI%": decodeURI,
      "%decodeURIComponent%": decodeURIComponent,
      "%encodeURI%": encodeURI,
      "%encodeURIComponent%": encodeURIComponent,
      "%Error%": Error,
      "%eval%": eval,
      // eslint-disable-line no-eval
      "%EvalError%": EvalError,
      "%Float32Array%": typeof Float32Array === "undefined" ? undefined2 : Float32Array,
      "%Float64Array%": typeof Float64Array === "undefined" ? undefined2 : Float64Array,
      "%FinalizationRegistry%": typeof FinalizationRegistry === "undefined" ? undefined2 : FinalizationRegistry,
      "%Function%": $Function,
      "%GeneratorFunction%": needsEval,
      "%Int8Array%": typeof Int8Array === "undefined" ? undefined2 : Int8Array,
      "%Int16Array%": typeof Int16Array === "undefined" ? undefined2 : Int16Array,
      "%Int32Array%": typeof Int32Array === "undefined" ? undefined2 : Int32Array,
      "%isFinite%": isFinite,
      "%isNaN%": isNaN,
      "%IteratorPrototype%": hasSymbols && getProto ? getProto(getProto([][Symbol.iterator]())) : undefined2,
      "%JSON%": typeof JSON === "object" ? JSON : undefined2,
      "%Map%": typeof Map === "undefined" ? undefined2 : Map,
      "%MapIteratorPrototype%": typeof Map === "undefined" || !hasSymbols || !getProto ? undefined2 : getProto((/* @__PURE__ */ new Map())[Symbol.iterator]()),
      "%Math%": Math,
      "%Number%": Number,
      "%Object%": Object,
      "%parseFloat%": parseFloat,
      "%parseInt%": parseInt,
      "%Promise%": typeof Promise === "undefined" ? undefined2 : Promise,
      "%Proxy%": typeof Proxy === "undefined" ? undefined2 : Proxy,
      "%RangeError%": RangeError,
      "%ReferenceError%": ReferenceError,
      "%Reflect%": typeof Reflect === "undefined" ? undefined2 : Reflect,
      "%RegExp%": RegExp,
      "%Set%": typeof Set === "undefined" ? undefined2 : Set,
      "%SetIteratorPrototype%": typeof Set === "undefined" || !hasSymbols || !getProto ? undefined2 : getProto((/* @__PURE__ */ new Set())[Symbol.iterator]()),
      "%SharedArrayBuffer%": typeof SharedArrayBuffer === "undefined" ? undefined2 : SharedArrayBuffer,
      "%String%": String,
      "%StringIteratorPrototype%": hasSymbols && getProto ? getProto(""[Symbol.iterator]()) : undefined2,
      "%Symbol%": hasSymbols ? Symbol : undefined2,
      "%SyntaxError%": $SyntaxError,
      "%ThrowTypeError%": ThrowTypeError,
      "%TypedArray%": TypedArray,
      "%TypeError%": $TypeError,
      "%Uint8Array%": typeof Uint8Array === "undefined" ? undefined2 : Uint8Array,
      "%Uint8ClampedArray%": typeof Uint8ClampedArray === "undefined" ? undefined2 : Uint8ClampedArray,
      "%Uint16Array%": typeof Uint16Array === "undefined" ? undefined2 : Uint16Array,
      "%Uint32Array%": typeof Uint32Array === "undefined" ? undefined2 : Uint32Array,
      "%URIError%": URIError,
      "%WeakMap%": typeof WeakMap === "undefined" ? undefined2 : WeakMap,
      "%WeakRef%": typeof WeakRef === "undefined" ? undefined2 : WeakRef,
      "%WeakSet%": typeof WeakSet === "undefined" ? undefined2 : WeakSet
    };
    if (getProto) {
      try {
        null.error;
      } catch (e) {
        errorProto = getProto(getProto(e));
        INTRINSICS["%Error.prototype%"] = errorProto;
      }
    }
    var errorProto;
    var doEval = function doEval2(name3) {
      var value;
      if (name3 === "%AsyncFunction%") {
        value = getEvalledConstructor("async function () {}");
      } else if (name3 === "%GeneratorFunction%") {
        value = getEvalledConstructor("function* () {}");
      } else if (name3 === "%AsyncGeneratorFunction%") {
        value = getEvalledConstructor("async function* () {}");
      } else if (name3 === "%AsyncGenerator%") {
        var fn = doEval2("%AsyncGeneratorFunction%");
        if (fn) {
          value = fn.prototype;
        }
      } else if (name3 === "%AsyncIteratorPrototype%") {
        var gen = doEval2("%AsyncGenerator%");
        if (gen && getProto) {
          value = getProto(gen.prototype);
        }
      }
      INTRINSICS[name3] = value;
      return value;
    };
    var LEGACY_ALIASES = {
      "%ArrayBufferPrototype%": ["ArrayBuffer", "prototype"],
      "%ArrayPrototype%": ["Array", "prototype"],
      "%ArrayProto_entries%": ["Array", "prototype", "entries"],
      "%ArrayProto_forEach%": ["Array", "prototype", "forEach"],
      "%ArrayProto_keys%": ["Array", "prototype", "keys"],
      "%ArrayProto_values%": ["Array", "prototype", "values"],
      "%AsyncFunctionPrototype%": ["AsyncFunction", "prototype"],
      "%AsyncGenerator%": ["AsyncGeneratorFunction", "prototype"],
      "%AsyncGeneratorPrototype%": ["AsyncGeneratorFunction", "prototype", "prototype"],
      "%BooleanPrototype%": ["Boolean", "prototype"],
      "%DataViewPrototype%": ["DataView", "prototype"],
      "%DatePrototype%": ["Date", "prototype"],
      "%ErrorPrototype%": ["Error", "prototype"],
      "%EvalErrorPrototype%": ["EvalError", "prototype"],
      "%Float32ArrayPrototype%": ["Float32Array", "prototype"],
      "%Float64ArrayPrototype%": ["Float64Array", "prototype"],
      "%FunctionPrototype%": ["Function", "prototype"],
      "%Generator%": ["GeneratorFunction", "prototype"],
      "%GeneratorPrototype%": ["GeneratorFunction", "prototype", "prototype"],
      "%Int8ArrayPrototype%": ["Int8Array", "prototype"],
      "%Int16ArrayPrototype%": ["Int16Array", "prototype"],
      "%Int32ArrayPrototype%": ["Int32Array", "prototype"],
      "%JSONParse%": ["JSON", "parse"],
      "%JSONStringify%": ["JSON", "stringify"],
      "%MapPrototype%": ["Map", "prototype"],
      "%NumberPrototype%": ["Number", "prototype"],
      "%ObjectPrototype%": ["Object", "prototype"],
      "%ObjProto_toString%": ["Object", "prototype", "toString"],
      "%ObjProto_valueOf%": ["Object", "prototype", "valueOf"],
      "%PromisePrototype%": ["Promise", "prototype"],
      "%PromiseProto_then%": ["Promise", "prototype", "then"],
      "%Promise_all%": ["Promise", "all"],
      "%Promise_reject%": ["Promise", "reject"],
      "%Promise_resolve%": ["Promise", "resolve"],
      "%RangeErrorPrototype%": ["RangeError", "prototype"],
      "%ReferenceErrorPrototype%": ["ReferenceError", "prototype"],
      "%RegExpPrototype%": ["RegExp", "prototype"],
      "%SetPrototype%": ["Set", "prototype"],
      "%SharedArrayBufferPrototype%": ["SharedArrayBuffer", "prototype"],
      "%StringPrototype%": ["String", "prototype"],
      "%SymbolPrototype%": ["Symbol", "prototype"],
      "%SyntaxErrorPrototype%": ["SyntaxError", "prototype"],
      "%TypedArrayPrototype%": ["TypedArray", "prototype"],
      "%TypeErrorPrototype%": ["TypeError", "prototype"],
      "%Uint8ArrayPrototype%": ["Uint8Array", "prototype"],
      "%Uint8ClampedArrayPrototype%": ["Uint8ClampedArray", "prototype"],
      "%Uint16ArrayPrototype%": ["Uint16Array", "prototype"],
      "%Uint32ArrayPrototype%": ["Uint32Array", "prototype"],
      "%URIErrorPrototype%": ["URIError", "prototype"],
      "%WeakMapPrototype%": ["WeakMap", "prototype"],
      "%WeakSetPrototype%": ["WeakSet", "prototype"]
    };
    var bind = require_function_bind();
    var hasOwn = require_hasown();
    var $concat = bind.call(Function.call, Array.prototype.concat);
    var $spliceApply = bind.call(Function.apply, Array.prototype.splice);
    var $replace = bind.call(Function.call, String.prototype.replace);
    var $strSlice = bind.call(Function.call, String.prototype.slice);
    var $exec = bind.call(Function.call, RegExp.prototype.exec);
    var rePropName = /[^%.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|%$))/g;
    var reEscapeChar = /\\(\\)?/g;
    var stringToPath = function stringToPath2(string) {
      var first = $strSlice(string, 0, 1);
      var last = $strSlice(string, -1);
      if (first === "%" && last !== "%") {
        throw new $SyntaxError("invalid intrinsic syntax, expected closing `%`");
      } else if (last === "%" && first !== "%") {
        throw new $SyntaxError("invalid intrinsic syntax, expected opening `%`");
      }
      var result = [];
      $replace(string, rePropName, function(match, number, quote, subString) {
        result[result.length] = quote ? $replace(subString, reEscapeChar, "$1") : number || match;
      });
      return result;
    };
    var getBaseIntrinsic = function getBaseIntrinsic2(name3, allowMissing) {
      var intrinsicName = name3;
      var alias;
      if (hasOwn(LEGACY_ALIASES, intrinsicName)) {
        alias = LEGACY_ALIASES[intrinsicName];
        intrinsicName = "%" + alias[0] + "%";
      }
      if (hasOwn(INTRINSICS, intrinsicName)) {
        var value = INTRINSICS[intrinsicName];
        if (value === needsEval) {
          value = doEval(intrinsicName);
        }
        if (typeof value === "undefined" && !allowMissing) {
          throw new $TypeError("intrinsic " + name3 + " exists, but is not available. Please file an issue!");
        }
        return {
          alias,
          name: intrinsicName,
          value
        };
      }
      throw new $SyntaxError("intrinsic " + name3 + " does not exist!");
    };
    module2.exports = function GetIntrinsic(name3, allowMissing) {
      if (typeof name3 !== "string" || name3.length === 0) {
        throw new $TypeError("intrinsic name must be a non-empty string");
      }
      if (arguments.length > 1 && typeof allowMissing !== "boolean") {
        throw new $TypeError('"allowMissing" argument must be a boolean');
      }
      if ($exec(/^%?[^%]*%?$/, name3) === null) {
        throw new $SyntaxError("`%` may not be present anywhere but at the beginning and end of the intrinsic name");
      }
      var parts = stringToPath(name3);
      var intrinsicBaseName = parts.length > 0 ? parts[0] : "";
      var intrinsic = getBaseIntrinsic("%" + intrinsicBaseName + "%", allowMissing);
      var intrinsicRealName = intrinsic.name;
      var value = intrinsic.value;
      var skipFurtherCaching = false;
      var alias = intrinsic.alias;
      if (alias) {
        intrinsicBaseName = alias[0];
        $spliceApply(parts, $concat([0, 1], alias));
      }
      for (var i = 1, isOwn = true; i < parts.length; i += 1) {
        var part = parts[i];
        var first = $strSlice(part, 0, 1);
        var last = $strSlice(part, -1);
        if ((first === '"' || first === "'" || first === "`" || (last === '"' || last === "'" || last === "`")) && first !== last) {
          throw new $SyntaxError("property names with quotes must have matching quotes");
        }
        if (part === "constructor" || !isOwn) {
          skipFurtherCaching = true;
        }
        intrinsicBaseName += "." + part;
        intrinsicRealName = "%" + intrinsicBaseName + "%";
        if (hasOwn(INTRINSICS, intrinsicRealName)) {
          value = INTRINSICS[intrinsicRealName];
        } else if (value != null) {
          if (!(part in value)) {
            if (!allowMissing) {
              throw new $TypeError("base intrinsic for " + name3 + " exists, but the property is not available.");
            }
            return void 0;
          }
          if ($gOPD && i + 1 >= parts.length) {
            var desc = $gOPD(value, part);
            isOwn = !!desc;
            if (isOwn && "get" in desc && !("originalValue" in desc.get)) {
              value = desc.get;
            } else {
              value = value[part];
            }
          } else {
            isOwn = hasOwn(value, part);
            value = value[part];
          }
          if (isOwn && !skipFurtherCaching) {
            INTRINSICS[intrinsicRealName] = value;
          }
        }
      }
      return value;
    };
  }
});

// ../../node_modules/has-property-descriptors/index.js
var require_has_property_descriptors = __commonJS({
  "../../node_modules/has-property-descriptors/index.js"(exports2, module2) {
    "use strict";
    var GetIntrinsic = require_get_intrinsic();
    var $defineProperty = GetIntrinsic("%Object.defineProperty%", true);
    var hasPropertyDescriptors = function hasPropertyDescriptors2() {
      if ($defineProperty) {
        try {
          $defineProperty({}, "a", { value: 1 });
          return true;
        } catch (e) {
          return false;
        }
      }
      return false;
    };
    hasPropertyDescriptors.hasArrayLengthDefineBug = function hasArrayLengthDefineBug() {
      if (!hasPropertyDescriptors()) {
        return null;
      }
      try {
        return $defineProperty([], "length", { value: 1 }).length !== 1;
      } catch (e) {
        return true;
      }
    };
    module2.exports = hasPropertyDescriptors;
  }
});

// ../../node_modules/gopd/index.js
var require_gopd = __commonJS({
  "../../node_modules/gopd/index.js"(exports2, module2) {
    "use strict";
    var GetIntrinsic = require_get_intrinsic();
    var $gOPD = GetIntrinsic("%Object.getOwnPropertyDescriptor%", true);
    if ($gOPD) {
      try {
        $gOPD([], "length");
      } catch (e) {
        $gOPD = null;
      }
    }
    module2.exports = $gOPD;
  }
});

// ../../node_modules/define-data-property/index.js
var require_define_data_property = __commonJS({
  "../../node_modules/define-data-property/index.js"(exports2, module2) {
    "use strict";
    var hasPropertyDescriptors = require_has_property_descriptors()();
    var GetIntrinsic = require_get_intrinsic();
    var $defineProperty = hasPropertyDescriptors && GetIntrinsic("%Object.defineProperty%", true);
    if ($defineProperty) {
      try {
        $defineProperty({}, "a", { value: 1 });
      } catch (e) {
        $defineProperty = false;
      }
    }
    var $SyntaxError = GetIntrinsic("%SyntaxError%");
    var $TypeError = GetIntrinsic("%TypeError%");
    var gopd = require_gopd();
    module2.exports = function defineDataProperty(obj, property, value) {
      if (!obj || typeof obj !== "object" && typeof obj !== "function") {
        throw new $TypeError("`obj` must be an object or a function`");
      }
      if (typeof property !== "string" && typeof property !== "symbol") {
        throw new $TypeError("`property` must be a string or a symbol`");
      }
      if (arguments.length > 3 && typeof arguments[3] !== "boolean" && arguments[3] !== null) {
        throw new $TypeError("`nonEnumerable`, if provided, must be a boolean or null");
      }
      if (arguments.length > 4 && typeof arguments[4] !== "boolean" && arguments[4] !== null) {
        throw new $TypeError("`nonWritable`, if provided, must be a boolean or null");
      }
      if (arguments.length > 5 && typeof arguments[5] !== "boolean" && arguments[5] !== null) {
        throw new $TypeError("`nonConfigurable`, if provided, must be a boolean or null");
      }
      if (arguments.length > 6 && typeof arguments[6] !== "boolean") {
        throw new $TypeError("`loose`, if provided, must be a boolean");
      }
      var nonEnumerable = arguments.length > 3 ? arguments[3] : null;
      var nonWritable = arguments.length > 4 ? arguments[4] : null;
      var nonConfigurable = arguments.length > 5 ? arguments[5] : null;
      var loose = arguments.length > 6 ? arguments[6] : false;
      var desc = !!gopd && gopd(obj, property);
      if ($defineProperty) {
        $defineProperty(obj, property, {
          configurable: nonConfigurable === null && desc ? desc.configurable : !nonConfigurable,
          enumerable: nonEnumerable === null && desc ? desc.enumerable : !nonEnumerable,
          value,
          writable: nonWritable === null && desc ? desc.writable : !nonWritable
        });
      } else if (loose || !nonEnumerable && !nonWritable && !nonConfigurable) {
        obj[property] = value;
      } else {
        throw new $SyntaxError("This environment does not support defining a property as non-configurable, non-writable, or non-enumerable.");
      }
    };
  }
});

// ../../node_modules/set-function-length/index.js
var require_set_function_length = __commonJS({
  "../../node_modules/set-function-length/index.js"(exports2, module2) {
    "use strict";
    var GetIntrinsic = require_get_intrinsic();
    var define = require_define_data_property();
    var hasDescriptors = require_has_property_descriptors()();
    var gOPD = require_gopd();
    var $TypeError = GetIntrinsic("%TypeError%");
    var $floor = GetIntrinsic("%Math.floor%");
    module2.exports = function setFunctionLength(fn, length) {
      if (typeof fn !== "function") {
        throw new $TypeError("`fn` is not a function");
      }
      if (typeof length !== "number" || length < 0 || length > 4294967295 || $floor(length) !== length) {
        throw new $TypeError("`length` must be a positive 32-bit integer");
      }
      var loose = arguments.length > 2 && !!arguments[2];
      var functionLengthIsConfigurable = true;
      var functionLengthIsWritable = true;
      if ("length" in fn && gOPD) {
        var desc = gOPD(fn, "length");
        if (desc && !desc.configurable) {
          functionLengthIsConfigurable = false;
        }
        if (desc && !desc.writable) {
          functionLengthIsWritable = false;
        }
      }
      if (functionLengthIsConfigurable || functionLengthIsWritable || !loose) {
        if (hasDescriptors) {
          define(fn, "length", length, true, true);
        } else {
          define(fn, "length", length);
        }
      }
      return fn;
    };
  }
});

// ../../node_modules/call-bind/index.js
var require_call_bind = __commonJS({
  "../../node_modules/call-bind/index.js"(exports2, module2) {
    "use strict";
    var bind = require_function_bind();
    var GetIntrinsic = require_get_intrinsic();
    var setFunctionLength = require_set_function_length();
    var $TypeError = GetIntrinsic("%TypeError%");
    var $apply = GetIntrinsic("%Function.prototype.apply%");
    var $call = GetIntrinsic("%Function.prototype.call%");
    var $reflectApply = GetIntrinsic("%Reflect.apply%", true) || bind.call($call, $apply);
    var $defineProperty = GetIntrinsic("%Object.defineProperty%", true);
    var $max = GetIntrinsic("%Math.max%");
    if ($defineProperty) {
      try {
        $defineProperty({}, "a", { value: 1 });
      } catch (e) {
        $defineProperty = null;
      }
    }
    module2.exports = function callBind(originalFunction) {
      if (typeof originalFunction !== "function") {
        throw new $TypeError("a function is required");
      }
      var func = $reflectApply(bind, $call, arguments);
      return setFunctionLength(
        func,
        1 + $max(0, originalFunction.length - (arguments.length - 1)),
        true
      );
    };
    var applyBind = function applyBind2() {
      return $reflectApply(bind, $apply, arguments);
    };
    if ($defineProperty) {
      $defineProperty(module2.exports, "apply", { value: applyBind });
    } else {
      module2.exports.apply = applyBind;
    }
  }
});

// ../../node_modules/call-bind/callBound.js
var require_callBound = __commonJS({
  "../../node_modules/call-bind/callBound.js"(exports2, module2) {
    "use strict";
    var GetIntrinsic = require_get_intrinsic();
    var callBind = require_call_bind();
    var $indexOf = callBind(GetIntrinsic("String.prototype.indexOf"));
    module2.exports = function callBoundIntrinsic(name3, allowMissing) {
      var intrinsic = GetIntrinsic(name3, !!allowMissing);
      if (typeof intrinsic === "function" && $indexOf(name3, ".prototype.") > -1) {
        return callBind(intrinsic);
      }
      return intrinsic;
    };
  }
});

// ../../node_modules/json-stable-stringify/index.js
var require_json_stable_stringify = __commonJS({
  "../../node_modules/json-stable-stringify/index.js"(exports2, module2) {
    "use strict";
    var jsonStringify = (typeof JSON !== "undefined" ? JSON : require_jsonify()).stringify;
    var isArray = require_isarray();
    var objectKeys = require_object_keys();
    var callBind = require_call_bind();
    var callBound = require_callBound();
    var $join = callBound("Array.prototype.join");
    var $push = callBound("Array.prototype.push");
    var strRepeat = function repeat(n, char) {
      var str2 = "";
      for (var i = 0; i < n; i += 1) {
        str2 += char;
      }
      return str2;
    };
    var defaultReplacer = function(parent, key, value) {
      return value;
    };
    module2.exports = function stableStringify(obj) {
      var opts = arguments.length > 1 ? arguments[1] : void 0;
      var space = opts && opts.space || "";
      if (typeof space === "number") {
        space = strRepeat(space, " ");
      }
      var cycles = !!opts && typeof opts.cycles === "boolean" && opts.cycles;
      var replacer = opts && opts.replacer ? callBind(opts.replacer) : defaultReplacer;
      var cmpOpt = typeof opts === "function" ? opts : opts && opts.cmp;
      var cmp = cmpOpt && function(node) {
        var get = cmpOpt.length > 2 && function get2(k) {
          return node[k];
        };
        return function(a, b) {
          return cmpOpt(
            { key: a, value: node[a] },
            { key: b, value: node[b] },
            get ? { __proto__: null, get } : void 0
          );
        };
      };
      var seen = [];
      return function stringify2(parent, key, node, level) {
        var indent = space ? "\n" + strRepeat(level, space) : "";
        var colonSeparator = space ? ": " : ":";
        if (node && node.toJSON && typeof node.toJSON === "function") {
          node = node.toJSON();
        }
        node = replacer(parent, key, node);
        if (node === void 0) {
          return;
        }
        if (typeof node !== "object" || node === null) {
          return jsonStringify(node);
        }
        if (isArray(node)) {
          var out = [];
          for (var i = 0; i < node.length; i++) {
            var item = stringify2(node, i, node[i], level + 1) || jsonStringify(null);
            $push(out, indent + space + item);
          }
          return "[" + $join(out, ",") + indent + "]";
        }
        if (seen.indexOf(node) !== -1) {
          if (cycles) {
            return jsonStringify("__cycle__");
          }
          throw new TypeError("Converting circular structure to JSON");
        } else {
          $push(seen, node);
        }
        var keys = objectKeys(node).sort(cmp && cmp(node));
        var out = [];
        for (var i = 0; i < keys.length; i++) {
          var key = keys[i];
          var value = stringify2(node, key, node[key], level + 1);
          if (!value) {
            continue;
          }
          var keyValue = jsonStringify(key) + colonSeparator + value;
          $push(out, indent + space + keyValue);
        }
        seen.splice(seen.indexOf(node), 1);
        return "{" + $join(out, ",") + indent + "}";
      }({ "": obj }, "", obj, 0);
    };
  }
});

// ../utils/src/arrayPartition.ts
var arrayPartition = (array, condition) => array.reduce(
  ([pass, fail], elem) => condition(elem) ? [[...pass, elem], fail] : [pass, [...fail, elem]],
  [[], []]
);

// ../utils/src/createDeferred.ts
var createDeferred = (id) => {
  let localResolve = () => {
  };
  let localReject = () => {
  };
  const promise = new Promise((resolve, reject) => {
    localResolve = resolve;
    localReject = reject;
  });
  return {
    id,
    resolve: localResolve,
    reject: localReject,
    promise
  };
};

// ../utils/src/createTimeoutPromise.ts
var createTimeoutPromise = (timeout) => new Promise((resolve) => setTimeout(resolve, timeout));

// ../utils/src/getSynchronize.ts
var getSynchronize = () => {
  let lock;
  return (action) => {
    const newLock = (lock ?? Promise.resolve()).catch(() => {
    }).then(action).finally(() => {
      if (lock === newLock) {
        lock = void 0;
      }
    });
    lock = newLock;
    return lock;
  };
};

// ../utils/src/getWeakRandomId.ts
var getWeakRandomId = (length) => {
  let id = "";
  const list = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  for (let i = 0; i < length; i++) {
    id += list.charAt(Math.floor(Math.random() * list.length));
  }
  return id;
};

// ../utils/src/isNotUndefined.ts
var isNotUndefined = (item) => typeof item !== "undefined";

// ../utils/src/typedEventEmitter.ts
var import_events = require("events");
var TypedEmitter = class extends import_events.EventEmitter {
  // implement at least one function
  listenerCount(eventName) {
    return super.listenerCount(eventName);
  }
};

// ../utils/src/logs.ts
var Log = class {
  prefix;
  enabled;
  css = "";
  messages;
  logWriter;
  MAX_ENTRIES = 100;
  constructor(prefix, enabled, logWriter) {
    this.prefix = prefix;
    this.enabled = enabled;
    this.messages = [];
    if (logWriter) {
      this.logWriter = logWriter;
    }
  }
  setColors(colors) {
    this.css = typeof window !== "undefined" && colors[this.prefix] ? colors[this.prefix] : "";
  }
  addMessage({ level, prefix, timestamp }, ...args) {
    const message = {
      level,
      prefix,
      css: this.css,
      message: args,
      timestamp: timestamp || Date.now()
    };
    this.messages.push(message);
    if (this.logWriter) {
      try {
        this.logWriter.add(message);
      } catch (err) {
        console.error("There was an error adding log message", err, message);
      }
    }
    if (this.messages.length > this.MAX_ENTRIES) {
      this.messages.shift();
    }
  }
  setWriter(logWriter) {
    this.logWriter = logWriter;
  }
  log(...args) {
    this.addMessage({ level: "log", prefix: this.prefix }, ...args);
    if (this.enabled) {
      console.log(`%c${this.prefix}`, this.css, ...args);
    }
  }
  error(...args) {
    this.addMessage({ level: "error", prefix: this.prefix }, ...args);
    if (this.enabled) {
      console.error(`%c${this.prefix}`, this.css, ...args);
    }
  }
  info(...args) {
    this.addMessage({ level: "info", prefix: this.prefix }, ...args);
    if (this.enabled) {
      console.info(`%c${this.prefix}`, this.css, ...args);
    }
  }
  warn(...args) {
    this.addMessage({ level: "warn", prefix: this.prefix }, ...args);
    if (this.enabled) {
      console.warn(`%c${this.prefix}`, this.css, ...args);
    }
  }
  debug(...args) {
    this.addMessage({ level: "debug", prefix: this.prefix }, ...args);
    if (this.enabled) {
      if (this.css) {
        console.log(`%c${this.prefix}`, this.css, ...args);
      } else {
        console.log(this.prefix, ...args);
      }
    }
  }
  getLog() {
    return this.messages;
  }
};

// ../utils/src/throttler.ts
var Throttler = class {
  delay;
  intervals;
  callbacks;
  constructor(delay) {
    this.delay = delay;
    this.intervals = {};
    this.callbacks = {};
  }
  throttle(id, callback) {
    if (this.intervals[id]) {
      this.callbacks[id] = callback;
    } else {
      callback();
      this.intervals[id] = setInterval(() => this.tick(id), this.delay);
    }
  }
  tick(id) {
    if (this.callbacks[id]) {
      this.callbacks[id]();
      delete this.callbacks[id];
    } else {
      this.cancel(id);
    }
  }
  cancel(id) {
    clearInterval(this.intervals[id]);
    delete this.intervals[id];
    delete this.callbacks[id];
  }
  dispose() {
    Object.keys(this.intervals).forEach(this.cancel, this);
  }
};

// src/http.ts
var import_promises = __toESM(require("fs/promises"));
var import_path = __toESM(require("path"));
var import_json_stable_stringify = __toESM(require_json_stable_stringify());

// ../node-utils/src/getFreePort.ts
var import_net = __toESM(require("net"));
var getFreePort = () => new Promise((resolve, reject) => {
  const server = import_net.default.createServer();
  server.unref();
  server.on("error", reject);
  server.listen(0, () => {
    const { port } = server.address();
    server.close(() => {
      resolve(port);
    });
  });
});

// ../node-utils/src/http.ts
var http = __toESM(require("http"));
var url = __toESM(require("url"));
var HttpServer = class extends TypedEmitter {
  server;
  logger;
  routes = [];
  emitter = this;
  port;
  sockets = {};
  constructor({ logger, port }) {
    super();
    this.port = port;
    this.logger = logger;
    this.server = http.createServer(this.onRequest);
  }
  get logName() {
    return `http: ${this.port || "unknown port"}`;
  }
  getServerAddress() {
    const address = this.server.address();
    if (!address || typeof address === "string") {
      throw new Error(`Unexpected server address: ${address}`);
    }
    return address;
  }
  getRouteAddress(pathname) {
    const address = this.getServerAddress();
    const route = this.routes.find((r) => r.pathname === pathname);
    if (!route) return;
    return `http://${address.address}:${address.port}${route.pathname}`;
  }
  getInfo() {
    const address = this.getServerAddress();
    return {
      url: `http://${address.address}:${address.port}`
    };
  }
  async start() {
    const port = this.port || (this.port = await getFreePort());
    return new Promise((resolve, reject) => {
      let nextSocketId = 0;
      this.server.on("connection", (socket) => {
        const socketId = nextSocketId++;
        this.sockets[socketId] = socket;
        socket.on("close", () => {
          delete this.sockets[socketId];
        });
      });
      this.server.on("error", (e) => {
        this.server.close();
        const errorCode = e.code;
        const errorMessage = errorCode === "EADDRINUSE" || errorCode === "EACCES" ? `Port ${port} already in use!` : `Start error code: ${errorCode}`;
        this.logger.error(errorMessage);
        return reject(new Error(`http-receiver: ${errorMessage}`));
      });
      this.server.listen(port, "127.0.0.1", void 0, () => {
        this.logger.info("Server started");
        const address = this.getServerAddress();
        if (address) {
          this.emitter.emit("server/listening", address);
        }
        return resolve(address);
      });
    });
  }
  stop() {
    this.emitter.removeAllListeners();
    return new Promise((resolve) => {
      this.emitter.emit("server/closing");
      this.server.closeAllConnections();
      this.server.close((err) => {
        if (err) {
          this.logger.info("trying to close server which was not running");
        }
        this.logger.info("Server stopped");
        this.emitter.emit("server/closed");
        resolve();
      });
      Object.values(this.sockets).forEach((socket) => {
        socket.destroy();
      });
    });
  }
  /**
   * split /a/:b/:c
   * to [a] and [:b, :c]
   */
  splitSegments(pathname) {
    const [baseSegments, paramsSegments] = arrayPartition(
      pathname.split("/").filter((segment) => segment),
      (segment) => !segment.includes(":")
    );
    return [baseSegments, paramsSegments];
  }
  registerRoute(pathname, method, handler) {
    const [baseSegments, paramsSegments] = this.splitSegments(pathname);
    const basePathname = baseSegments.join("/");
    this.routes.push({
      method,
      pathname: `/${basePathname}`,
      params: paramsSegments,
      handler
    });
  }
  post(pathname, handler) {
    this.registerRoute(pathname, "POST", handler);
  }
  get(pathname, handler) {
    this.registerRoute(pathname, "GET", handler);
  }
  // PUT, DELETE etc are not used anywhere in our codebase, so no need to implement them now
  /**
   * Register common handlers that are run for all requests before route handlers
   */
  use(handler) {
    this.routes.push({
      method: "*",
      pathname: "*",
      handler,
      params: []
    });
  }
  /**
   * pathname could be /a/b/c/d
   * return route with highest number of matching segments
   */
  findBestMatchingRoute = (pathname, method = "GET") => {
    const segments = pathname.split("/").map((segment) => segment || "/");
    const routes = this.routes.filter((r) => r.method === method || r.method === "*");
    const match = routes.reduce(
      (acc, route) => {
        const routeSegments = route.pathname.split("/").map((segment) => segment || "/");
        const matchedSegments = segments.filter(
          (segment, index) => segment === routeSegments[index]
        );
        if (matchedSegments.length > acc.matchedSegments.length) {
          return { route, matchedSegments };
        }
        return acc;
      },
      { route: void 0, matchedSegments: [] }
    );
    return match.route;
  };
  /**
   * Entry point for handling requests
   */
  onRequest = (request, response) => {
    if (!request.url) {
      this.logger.warn("Unexpected incoming message (no url)");
      this.emitter.emit("server/error", "Unexpected incoming message");
      return;
    }
    request.on("aborted", () => {
      this.logger.info(`Request ${request.method} ${request.url} aborted`);
    });
    const { pathname } = url.parse(request.url, true);
    if (!pathname) {
      const msg = `url ${request.url} could not be parsed`;
      this.emitter.emit("server/error", msg);
      this.logger.warn(msg);
      return;
    }
    this.logger.info(`Handling request for ${request.method} ${pathname}`);
    const route = this.findBestMatchingRoute(pathname, request.method);
    if (!route) {
      this.emitter.emit("server/error", `Route not found for ${request.method} ${pathname}`);
      this.logger.warn(`Route not found for ${request.method} ${pathname}`);
      return;
    }
    if (!route.handler.length) {
      this.emitter.emit("server/error", `No handlers registered for route ${pathname}`);
      this.logger.warn(`No handlers registered for route ${pathname}`);
      return;
    }
    const paramsSegments = pathname.replace(route.pathname, "").split("/").filter((segment) => segment);
    const requestWithParams = request;
    requestWithParams.params = route.params.reduce(
      (acc, param, index) => {
        acc[param.replace(":", "")] = paramsSegments[index];
        return acc;
      },
      {}
    );
    const handlers = [
      ...this.routes.filter((r) => r.method === "*" && r.pathname === "*").flatMap((r) => r.handler),
      ...route.handler
    ];
    const run = ([handler, ...rest]) => (req, res) => handler?.(req, res, run(rest), { logger: this.logger });
    run(handlers)(requestWithParams, response);
  };
};
var checkOrigin = ({
  request,
  allowedOrigin,
  pathname,
  logger
}) => {
  const { origin: origin2 } = request.headers;
  const origins = allowedOrigin ?? [];
  let isOriginAllowed = false;
  if (origins.includes("*")) {
    isOriginAllowed = true;
  }
  if (origin2) {
    isOriginAllowed = origins.some((o) => {
      try {
        return new URL(origin2).hostname.endsWith(new URL(o).hostname);
      } catch (error2) {
        logger.error(`Failed parsing URL: ${error2}`);
      }
    });
  }
  if (!isOriginAllowed) {
    logger.warn(`Origin rejected for ${pathname}`);
    logger.warn(`- Received: origin: '${origin2}'`);
    logger.warn(`- Allowed origins: ${origins.map((o) => `'${o}'`).join(", ")}`);
    return false;
  }
  return true;
};
var allowOrigins = (allowedOrigin) => (request, _response, next, { logger }) => {
  if (checkOrigin({
    request,
    allowedOrigin,
    pathname: request.url,
    logger
  })) {
    next(request, _response);
  }
};
var parseBodyTextHelper = (request) => new Promise((resolve) => {
  const tmp = [];
  request.on("data", (chunk) => {
    tmp.push(chunk);
  }).on("end", () => {
    const body = Buffer.concat(tmp).toString();
    resolve(body);
  });
});
var parseBodyJSON = (request, response, next) => {
  parseBodyTextHelper(request).then((body) => JSON.parse(body)).then((body) => {
    next({ ...request, body }, response);
  }).catch((error2) => {
    response.statusCode = 400;
    response.end(JSON.stringify({ error: `Invalid json body: ${error2.message}` }));
  });
};
var parseBodyText = (request, response, next) => {
  parseBodyTextHelper(request).then((body) => {
    next({ ...request, body }, response);
  });
};

// ../transport/src/utils/bridgeProtocolMessage.ts
function validateProtocolMessage(body, withData = true) {
  const isHex = (s) => /^[0-9A-Fa-f]+$/g.test(s);
  const isValidProtocol = (s) => s === "v1" || s === "bridge";
  if (typeof body === "string") {
    if (withData && isHex(body) || !withData && !body.length) {
      return {
        data: body
      };
    }
  }
  let json;
  if (typeof body === "object") {
    json = body;
  } else {
    try {
      json = JSON.parse(body);
    } catch {
    }
  }
  if (!json) {
    throw new Error("Invalid BridgeProtocolMessage body");
  }
  if (typeof json.protocol !== "string" || !isValidProtocol(json.protocol)) {
    throw new Error("Invalid BridgeProtocolMessage protocol");
  }
  if (withData && (typeof json.data !== "string" || !isHex(json.data))) {
    throw new Error("Invalid BridgeProtocolMessage data");
  }
  return {
    protocol: json.protocol,
    data: json.data
  };
}
function createProtocolMessage(body, protocol) {
  let data;
  if (Buffer.isBuffer(body)) {
    data = body.toString("hex");
  }
  if (typeof body === "string") {
    data = body;
  }
  if (typeof data !== "string") {
    data = "";
  }
  if (!protocol) {
    return data;
  }
  return JSON.stringify({
    protocol: typeof protocol === "string" ? protocol : protocol.name,
    data
  });
}

// src/core.ts
var import_usb = require("usb");

// ../protocol/src/protocol-v1/index.ts
var protocol_v1_exports = {};
__export(protocol_v1_exports, {
  decode: () => decode,
  encode: () => encode,
  getChunkHeader: () => getChunkHeader,
  name: () => name
});

// ../protocol/src/errors.ts
var PROTOCOL_MALFORMED = "Malformed protocol format";

// ../protocol/src/protocol-v1/constants.ts
var MESSAGE_MAGIC_HEADER_BYTE = 63;
var MESSAGE_HEADER_BYTE = 35;
var HEADER_SIZE = 1 + 1 + 1 + 2 + 4;

// ../protocol/src/protocol-v1/decode.ts
var readHeaderChunked = (buffer) => {
  const magic = buffer.readUInt8();
  const sharp1 = buffer.readUInt8(1);
  const sharp2 = buffer.readUInt8(2);
  const messageType = buffer.readUInt16BE(3);
  const length = buffer.readUInt32BE(5);
  return { magic, sharp1, sharp2, messageType, length };
};
var decode = (bytes) => {
  if (bytes.byteLength === 0) {
    console.error("protocol-v1: decode: received empty buffer");
  }
  const { magic, sharp1, sharp2, messageType, length } = readHeaderChunked(bytes);
  if (magic !== MESSAGE_MAGIC_HEADER_BYTE || sharp1 !== MESSAGE_HEADER_BYTE || sharp2 !== MESSAGE_HEADER_BYTE) {
    throw new Error(PROTOCOL_MALFORMED);
  }
  return {
    length,
    messageType,
    payload: bytes.subarray(HEADER_SIZE)
  };
};

// ../protocol/src/protocol-v1/encode.ts
var getChunkHeader = (_data) => {
  const header = Buffer.alloc(1);
  header.writeUInt8(MESSAGE_MAGIC_HEADER_BYTE);
  return header;
};
var encode = (data, options) => {
  const { messageType } = options;
  if (typeof messageType === "string") {
    throw new Error(`Unsupported message type ${messageType}`);
  }
  const fullSize = HEADER_SIZE + data.length;
  const encodedBuffer = Buffer.alloc(fullSize);
  encodedBuffer.writeUInt8(MESSAGE_MAGIC_HEADER_BYTE, 0);
  encodedBuffer.writeUInt8(MESSAGE_HEADER_BYTE, 1);
  encodedBuffer.writeUInt8(MESSAGE_HEADER_BYTE, 2);
  encodedBuffer.writeUInt16BE(messageType, 3);
  encodedBuffer.writeUInt32BE(data.length, 5);
  data.copy(encodedBuffer, HEADER_SIZE);
  return encodedBuffer;
};

// ../protocol/src/protocol-v1/index.ts
var name = "v1";

// ../protocol/src/protocol-bridge/index.ts
var protocol_bridge_exports = {};
__export(protocol_bridge_exports, {
  decode: () => decode2,
  encode: () => encode2,
  getChunkHeader: () => getChunkHeader2,
  name: () => name2
});

// ../protocol/src/protocol-bridge/constants.ts
var HEADER_SIZE2 = 2 + 4;

// ../protocol/src/protocol-bridge/decode.ts
var readHeader = (buffer) => {
  const messageType = buffer.readUInt16BE();
  const length = buffer.readUInt32BE(2);
  return { messageType, length };
};
var decode2 = (bytes) => {
  const { messageType, length } = readHeader(bytes);
  return {
    messageType,
    length,
    payload: bytes.subarray(HEADER_SIZE2)
  };
};

// ../protocol/src/protocol-bridge/encode.ts
var getChunkHeader2 = (_data) => Buffer.alloc(0);
var encode2 = (data, options) => {
  const { messageType } = options;
  if (typeof messageType === "string") {
    throw new Error(`Unsupported message type ${messageType}`);
  }
  const encodedBuffer = Buffer.alloc(HEADER_SIZE2 + data.length);
  encodedBuffer.writeUInt16BE(messageType);
  encodedBuffer.writeUInt32BE(data.length, 2);
  data.copy(encodedBuffer, HEADER_SIZE2);
  return encodedBuffer;
};

// ../protocol/src/protocol-bridge/index.ts
var name2 = "bridge";

// ../transport/src/errors.ts
var INTERFACE_UNABLE_TO_OPEN_DEVICE = "Unable to open device";
var INTERFACE_UNABLE_TO_CLOSE_DEVICE = "Unable to close device";
var INTERFACE_DATA_TRANSFER = "A transfer error has occurred.";
var DEVICE_NOT_FOUND = "device not found";
var SESSION_WRONG_PREVIOUS = "wrong previous session";
var SESSION_NOT_FOUND = "session not found";
var DESCRIPTOR_NOT_FOUND = "descriptor not found";
var DEVICE_DISCONNECTED_DURING_ACTION = "device disconnected during action";
var OTHER_CALL_IN_PROGRESS = "other call in progress";
var UNEXPECTED_ERROR = "unexpected error";
var ABORTED_BY_SIGNAL = "Aborted by signal";

// ../transport/src/utils/result.ts
var success = (payload) => ({
  success: true,
  payload
});
var error = ({ error: error2, message }) => ({
  success: false,
  error: error2,
  message
});
var unknownError = (err, expectedErrors = []) => {
  const expectedErr = expectedErrors.find((eE) => eE === err.message);
  if (expectedErr) {
    return error({ error: expectedErr });
  }
  return {
    success: false,
    error: UNEXPECTED_ERROR,
    message: err.message
  };
};

// ../transport/src/utils/receive.ts
async function receive(receiver, protocol) {
  const readResult = await receiver();
  if (!readResult.success) {
    return readResult;
  }
  const data = readResult.payload;
  const { length, messageType, payload } = protocol.decode(data);
  let result = Buffer.alloc(length);
  const chunkHeader = protocol.getChunkHeader(Buffer.from(data));
  payload.copy(result);
  let offset = payload.length;
  while (offset < length) {
    const readResult2 = await receiver();
    if (!readResult2.success) {
      return readResult2;
    }
    const data2 = readResult2.payload;
    Buffer.from(data2).copy(result, offset, chunkHeader.byteLength);
    offset += data2.byteLength - chunkHeader.byteLength;
  }
  return success({ messageType, payload: result });
}

// ../transport/src/utils/send.ts
var createChunks = (data, chunkHeader, chunkSize) => {
  if (!chunkSize || data.byteLength <= chunkSize) {
    const buffer = Buffer.alloc(Math.max(chunkSize, data.byteLength));
    data.copy(buffer);
    return [buffer];
  }
  const chunks = [data.subarray(0, chunkSize)];
  let position = chunkSize;
  while (position < data.byteLength) {
    const sliceEnd = Math.min(position + chunkSize - chunkHeader.byteLength, data.byteLength);
    const slice = data.subarray(position, sliceEnd);
    const chunk = Buffer.concat([chunkHeader, slice]);
    chunks.push(Buffer.alloc(chunkSize).fill(chunk, 0, chunk.byteLength));
    position = sliceEnd;
  }
  return chunks;
};
var sendChunks = async (chunks, apiWrite) => {
  for (let i = 0; i < chunks.length; i++) {
    const result = await apiWrite(chunks[i]);
    if (!result.success) {
      return result;
    }
  }
  return { success: true, payload: void 0 };
};

// ../transport/src/sessions/background.ts
var lockDuration = 1e3 * 4;
var SessionsBackground = class extends TypedEmitter {
  /**
   * Dictionary where key is path and value is Descriptor
   */
  descriptors = {};
  pathInternalPathPublicMap = {};
  // if lock is set, somebody is doing something with device. we have to wait
  locksQueue = [];
  locksTimeoutQueue = [];
  lastSessionId = 0;
  lastPathId = 0;
  async handleMessage(message) {
    let result;
    try {
      switch (message.type) {
        case "handshake":
          result = this.handshake();
          break;
        case "enumerateDone":
          result = await this.enumerateDone(message.payload);
          break;
        case "acquireIntent":
          result = await this.acquireIntent(message.payload);
          break;
        case "acquireDone":
          result = await this.acquireDone(message.payload);
          break;
        case "getSessions":
          result = await this.getSessions();
          break;
        case "releaseIntent":
          result = await this.releaseIntent(message.payload);
          break;
        case "releaseDone":
          result = await this.releaseDone(message.payload);
          break;
        case "getPathBySession":
          result = this.getPathBySession(message.payload);
          break;
        case "dispose":
          this.dispose();
          break;
        default:
          throw new Error(UNEXPECTED_ERROR);
      }
      result = JSON.parse(JSON.stringify({ ...result, id: message.id }));
      return result;
    } catch (err) {
      console.error("Session background error", err);
      return {
        ...this.error(UNEXPECTED_ERROR),
        id: message.type
      };
    } finally {
      if (result && result.success && result.payload && "descriptors" in result.payload) {
        const { descriptors } = result.payload;
        setTimeout(() => this.emit("descriptors", Object.values(descriptors)), 0);
      }
    }
  }
  handshake() {
    return this.success(void 0);
  }
  /**
   * enumerate done
   * - caller informs about current descriptors
   */
  enumerateDone(payload) {
    const disconnectedDevices = Object.keys(this.descriptors).filter(
      (pathInternal) => !payload.descriptors.find((d) => d.path === pathInternal)
    );
    disconnectedDevices.forEach((d) => {
      delete this.descriptors[d];
      delete this.pathInternalPathPublicMap[d];
    });
    payload.descriptors.forEach((d) => {
      if (!this.pathInternalPathPublicMap[d.path]) {
        this.pathInternalPathPublicMap[d.path] = `${this.lastPathId += 1}`;
      }
      if (!this.descriptors[d.path]) {
        this.descriptors[d.path] = {
          ...d,
          path: this.pathInternalPathPublicMap[d.path],
          session: null
        };
      }
    });
    return Promise.resolve(
      this.success({
        descriptors: Object.values(this.descriptors)
      })
    );
  }
  /**
   * acquire intent
   */
  async acquireIntent(payload) {
    const pathInternal = this.getInternal(payload.path);
    if (!pathInternal) {
      return this.error(DESCRIPTOR_NOT_FOUND);
    }
    const previous = this.descriptors[pathInternal]?.session;
    if (payload.previous && payload.previous !== previous) {
      return this.error(SESSION_WRONG_PREVIOUS);
    }
    if (!this.descriptors[pathInternal]) {
      return this.error(DESCRIPTOR_NOT_FOUND);
    }
    await this.waitInQueue();
    if (previous !== this.descriptors[pathInternal]?.session) {
      this.clearLock();
      return this.error(SESSION_WRONG_PREVIOUS);
    }
    const unconfirmedSessions = JSON.parse(JSON.stringify(this.descriptors));
    this.lastSessionId++;
    unconfirmedSessions[pathInternal].session = `${this.lastSessionId}`;
    return this.success({
      session: unconfirmedSessions[pathInternal].session,
      path: pathInternal,
      descriptors: Object.values(unconfirmedSessions)
    });
  }
  /**
   * client notified backend that he is able to talk to device
   * - assign client a new "session". this session will be used in all subsequent communication
   */
  acquireDone(payload) {
    this.clearLock();
    const pathInternal = this.getInternal(payload.path);
    if (!pathInternal || !this.descriptors[pathInternal]) {
      return this.error(DESCRIPTOR_NOT_FOUND);
    }
    this.descriptors[pathInternal].session = `${this.lastSessionId}`;
    return Promise.resolve(
      this.success({
        descriptors: Object.values(this.descriptors)
      })
    );
  }
  async releaseIntent(payload) {
    const pathResult = this.getPathBySession({ session: payload.session });
    if (!pathResult.success) {
      return pathResult;
    }
    const { path: path2 } = pathResult.payload;
    await this.waitInQueue();
    return this.success({ path: path2 });
  }
  releaseDone(payload) {
    this.descriptors[payload.path].session = null;
    this.clearLock();
    return Promise.resolve(this.success({ descriptors: Object.values(this.descriptors) }));
  }
  getSessions() {
    return Promise.resolve(this.success({ descriptors: Object.values(this.descriptors) }));
  }
  getPathBySession({ session }) {
    const path2 = Object.keys(this.descriptors).find(
      (pathKey) => this.descriptors[pathKey]?.session === session
    );
    if (!path2) {
      return this.error(SESSION_NOT_FOUND);
    }
    return this.success({ path: path2 });
  }
  startLock() {
    const dfd = createDeferred();
    const timeout = setTimeout(() => {
      dfd.resolve(void 0);
    }, lockDuration);
    this.locksQueue.push({ id: timeout, dfd });
    this.locksTimeoutQueue.push(timeout);
    return this.locksQueue.length - 1;
  }
  clearLock() {
    const lock = this.locksQueue[0];
    if (lock) {
      this.locksQueue[0].dfd.resolve(void 0);
      this.locksQueue.shift();
      clearTimeout(this.locksTimeoutQueue[0]);
      this.locksTimeoutQueue.shift();
    }
  }
  async waitForUnlocked(myIndex) {
    if (myIndex > 0) {
      const beforeMe = this.locksQueue.slice(0, myIndex);
      if (beforeMe.length) {
        await Promise.all(beforeMe.map((lock) => lock.dfd.promise));
      }
    }
  }
  async waitInQueue() {
    const myIndex = this.startLock();
    await this.waitForUnlocked(myIndex);
  }
  success(payload) {
    return {
      success: true,
      payload
    };
  }
  error(error2) {
    return {
      success: false,
      error: error2
    };
  }
  getInternal(pathPublic) {
    return Object.keys(this.pathInternalPathPublicMap).find(
      (internal) => this.pathInternalPathPublicMap[internal] === pathPublic
    );
  }
  dispose() {
    this.locksQueue.forEach((lock) => clearTimeout(lock.id));
    this.locksTimeoutQueue.forEach((timeout) => clearTimeout(timeout));
    this.descriptors = {};
    this.lastSessionId = 0;
  }
};

// ../transport/src/sessions/client.ts
var SessionsClient = class extends TypedEmitter {
  // request method responsible for communication with sessions background.
  request;
  // used only for debugging - discriminating sessions clients in sessions background log
  caller = getWeakRandomId(3);
  id;
  constructor({
    requestFn,
    registerBackgroundCallbacks
  }) {
    super();
    this.id = 0;
    this.request = (params) => {
      params.caller = this.caller;
      params.id = this.id;
      this.id++;
      return requestFn(params);
    };
    if (registerBackgroundCallbacks) {
      registerBackgroundCallbacks((descriptors) => {
        this.emit("descriptors", descriptors);
      });
    }
  }
  handshake() {
    return this.request({ type: "handshake" });
  }
  enumerateDone(payload) {
    return this.request({ type: "enumerateDone", payload });
  }
  acquireIntent(payload) {
    return this.request({ type: "acquireIntent", payload });
  }
  acquireDone(payload) {
    return this.request({ type: "acquireDone", payload });
  }
  releaseIntent(payload) {
    return this.request({ type: "releaseIntent", payload });
  }
  releaseDone(payload) {
    return this.request({ type: "releaseDone", payload });
  }
  getSessions() {
    return this.request({ type: "getSessions" });
  }
  getPathBySession(payload) {
    return this.request({ type: "getPathBySession", payload });
  }
  dispose() {
    this.removeAllListeners("descriptors");
    return this.request({ type: "dispose" });
  }
};

// ../transport/src/api/abstract.ts
var AbstractApi = class extends TypedEmitter {
  logger;
  listening = false;
  lock = {};
  constructor({ logger }) {
    super();
    this.logger = logger;
  }
  success(payload) {
    return success(payload);
  }
  error(payload) {
    return error(payload);
  }
  unknownError(err, expectedErrors = []) {
    this.logger?.error("transport: abstract api: unknown error", err);
    return unknownError(err, expectedErrors);
  }
  synchronize = getSynchronize();
  /**
   * call this to ensure single access to transport api.
   */
  requestAccess({ lock, path: path2 }) {
    if (!this.lock[path2]) {
      this.lock[path2] = { read: false, write: false };
    }
    if (this.lock[path2].read && lock.read || this.lock[path2].write && lock.write) {
      return this.error({ error: OTHER_CALL_IN_PROGRESS });
    }
    this.lock[path2] = {
      read: this.lock[path2].read || lock.read,
      write: this.lock[path2].write || lock.write
    };
    return this.success(void 0);
  }
  /**
   * 1. merges lock with current lock
   * 2. runs provided function
   * 3. clears its own lock
   */
  runInIsolation = async ({ lock, path: path2 }, fn) => {
    const accessRes = this.requestAccess({ lock, path: path2 });
    if (!accessRes.success) {
      return accessRes;
    }
    try {
      return await this.synchronize(fn);
    } catch (err) {
      this.logger?.error("transport: abstract api: runInIsolation error", err);
      return this.unknownError(err);
    } finally {
      this.lock[path2] = {
        read: lock.read ? false : this.lock[path2].read,
        write: lock.write ? false : this.lock[path2].write
      };
    }
  };
};

// ../transport/src/constants.ts
var CONFIGURATION_ID = 1;
var INTERFACE_ID = 0;
var ENDPOINT_ID = 1;
var DEBUGLINK_INTERFACE_ID = 1;
var DEBUGLINK_ENDPOINT_ID = 2;
var T1_HID_VENDOR = 21324;
var T1_HID_PRODUCT = 1;
var WEBUSB_FIRMWARE_PRODUCT = 21441;
var WEBUSB_BOOTLOADER_PRODUCT = 21440;
var TREZOR_USB_DESCRIPTORS = [
  // TREZOR v1
  // won't get opened, but we can show error at least
  { vendorId: 21324, productId: T1_HID_PRODUCT },
  // TREZOR webusb Bootloader
  { vendorId: 4617, productId: WEBUSB_BOOTLOADER_PRODUCT },
  // TREZOR webusb Firmware
  { vendorId: 4617, productId: WEBUSB_FIRMWARE_PRODUCT }
];

// ../transport/src/api/usb.ts
var INTERFACE_DEVICE_DISCONNECTED = "The device was disconnected.";
var UsbApi = class extends AbstractApi {
  chunkSize = 64;
  devices = [];
  usbInterface;
  forceReadSerialOnConnect;
  abortController = new AbortController();
  debugLink;
  constructor({ usbInterface, logger, forceReadSerialOnConnect, debugLink }) {
    super({ logger });
    this.usbInterface = usbInterface;
    this.forceReadSerialOnConnect = forceReadSerialOnConnect;
    this.debugLink = debugLink;
  }
  listen() {
    this.usbInterface.onconnect = (event) => {
      this.logger?.debug(`usb: onconnect: ${this.formatDeviceForLog(event.device)}`);
      this.synchronize(() => {
        this.createDevices([event.device], this.abortController.signal).then((newDevices) => {
          this.devices = [...this.devices, ...newDevices];
          this.emit("transport-interface-change", this.devicesToDescriptors());
        }).catch((err) => {
          this.logger?.error(`usb: createDevices error: ${err.message}`);
        });
      });
    };
    this.usbInterface.ondisconnect = (event) => {
      const { device } = event;
      if (!device.serialNumber) {
        this.logger?.debug(
          `usb: ondisconnect: device without serial number:, ${device.productName}, ${device.manufacturerName}`
        );
        return;
      }
      const index = this.devices.findIndex((d) => d.path === device.serialNumber);
      if (index > -1) {
        this.devices.splice(index, 1);
        this.emit("transport-interface-change", this.devicesToDescriptors());
      } else {
        this.emit("transport-interface-error", DEVICE_NOT_FOUND);
        this.logger?.error("usb: device that should be removed does not exist in state");
      }
    };
  }
  formatDeviceForLog(device) {
    return JSON.stringify({
      productName: device.productName,
      manufacturerName: device.manufacturerName,
      serialNumber: device.serialNumber,
      vendorId: device.vendorId,
      productId: device.productId,
      deviceVersionMajor: device.deviceVersionMajor,
      deviceVersionMinor: device.deviceVersionMinor,
      opened: device.opened
    });
  }
  matchDeviceType(device) {
    const isBootloader = device.productId === WEBUSB_BOOTLOADER_PRODUCT;
    if (device.deviceVersionMajor === 2) {
      if (isBootloader) {
        return 4 /* TypeT2Boot */;
      } else {
        return 3 /* TypeT2 */;
      }
    } else {
      if (isBootloader) {
        return 2 /* TypeT1WebusbBoot */;
      } else {
        return 1 /* TypeT1Webusb */;
      }
    }
  }
  devicesToDescriptors() {
    return this.devices.map((d) => ({
      path: d.path,
      type: this.matchDeviceType(d.device),
      product: d.device.productId,
      vendor: d.device.vendorId
    }));
  }
  abortableMethod(method, { signal, onAbort }) {
    if (!signal) {
      return method();
    }
    if (signal.aborted) {
      return Promise.reject(new Error(ABORTED_BY_SIGNAL));
    }
    const dfd = createDeferred();
    const abortListener = async () => {
      this.logger?.debug("usb: abortableMethod onAbort start");
      try {
        await onAbort?.();
      } catch {
      }
      this.logger?.debug("usb: abortableMethod onAbort done");
      dfd.reject(new Error(ABORTED_BY_SIGNAL));
    };
    signal?.addEventListener("abort", abortListener);
    const methodPromise = method().catch((error2) => {
      this.logger?.debug(`usb: abortableMethod method() aborted: ${signal.aborted} ${error2}`);
      if (signal.aborted) {
        return dfd.promise;
      }
      dfd.reject(error2);
      throw error2;
    });
    return Promise.race([methodPromise, dfd.promise]).then((r) => {
      dfd.resolve(r);
      return r;
    }).finally(() => {
      signal?.removeEventListener("abort", abortListener);
    });
  }
  enumerate(signal) {
    return this.synchronize(async () => {
      try {
        this.logger?.debug("usb: enumerate");
        const devices = await this.abortableMethod(() => this.usbInterface.getDevices(), {
          signal
        });
        this.devices = await this.createDevices(devices, signal);
        return this.success(this.devicesToDescriptors());
      } catch (err) {
        return this.unknownError(err);
      }
    });
  }
  async read(path2, signal) {
    const device = this.findDevice(path2);
    if (!device) {
      return this.error({ error: DEVICE_NOT_FOUND });
    }
    try {
      this.logger?.debug("usb: device.transferIn");
      const res = await this.abortableMethod(
        () => device.transferIn(
          this.debugLink ? DEBUGLINK_ENDPOINT_ID : ENDPOINT_ID,
          this.chunkSize
        ),
        { signal, onAbort: () => device?.reset() }
      );
      this.logger?.debug(
        `usb: device.transferIn done. status: ${res.status}, byteLength: ${res.data?.byteLength}. device: ${this.formatDeviceForLog(device)}`
      );
      if (!res.data?.byteLength) {
        return this.error({ error: INTERFACE_DATA_TRANSFER });
      }
      return this.success(Buffer.from(res.data.buffer));
    } catch (err) {
      this.logger?.error(`usb: device.transferIn error ${err}`);
      if (err.message === INTERFACE_DEVICE_DISCONNECTED) {
        return this.error({ error: DEVICE_DISCONNECTED_DURING_ACTION });
      }
      return this.unknownError(err, [
        ABORTED_BY_SIGNAL,
        INTERFACE_DATA_TRANSFER
      ]);
    }
  }
  async write(path2, buffer, signal) {
    const device = this.findDevice(path2);
    if (!device) {
      return this.error({ error: DEVICE_NOT_FOUND });
    }
    const newArray = new Uint8Array(this.chunkSize);
    newArray.set(new Uint8Array(buffer));
    try {
      this.logger?.debug("usb: device.transferOut");
      const result = await this.abortableMethod(
        () => device.transferOut(
          this.debugLink ? DEBUGLINK_ENDPOINT_ID : ENDPOINT_ID,
          newArray
        ),
        { signal, onAbort: () => device?.reset() }
      );
      this.logger?.debug(
        `usb: device.transferOut done. device: ${this.formatDeviceForLog(device)}`
      );
      if (result.status !== "ok") {
        this.logger?.error(`usb: device.transferOut status not ok: ${result.status}`);
        throw new Error("transfer out status not ok");
      }
      return this.success(void 0);
    } catch (err) {
      this.logger?.error(`usb: device.transferOut error ${err}`);
      if (err.message === INTERFACE_DEVICE_DISCONNECTED) {
        return this.error({ error: DEVICE_DISCONNECTED_DURING_ACTION });
      }
      return this.error({ error: INTERFACE_DATA_TRANSFER, message: err.message });
    }
  }
  async openDevice(path2, first, signal) {
    for (let i = 0; i < 5; i++) {
      this.logger?.debug(`usb: openDevice attempt ${i}`);
      const res = await this.openInternal(path2, first, signal);
      if (res.success || signal?.aborted) {
        return res;
      }
      await createTimeoutPromise(100 * i);
    }
    return this.openInternal(path2, first, signal);
  }
  async openInternal(path2, first, signal) {
    const device = this.findDevice(path2);
    if (!device) {
      return this.error({ error: DEVICE_NOT_FOUND });
    }
    try {
      this.logger?.debug(`usb: device.open`);
      await this.abortableMethod(() => device.open(), { signal });
      this.logger?.debug(`usb: device.open done. device: ${this.formatDeviceForLog(device)}`);
    } catch (err) {
      this.logger?.error(`usb: device.open error ${err}`);
      return this.error({
        error: INTERFACE_UNABLE_TO_OPEN_DEVICE,
        message: err.message
      });
    }
    if (first) {
      try {
        this.logger?.debug(`usb: device.selectConfiguration ${CONFIGURATION_ID}`);
        await this.abortableMethod(() => device.selectConfiguration(CONFIGURATION_ID), {
          signal
        });
        this.logger?.debug(
          `usb: device.selectConfiguration done: ${CONFIGURATION_ID}. device: ${this.formatDeviceForLog(device)}`
        );
      } catch (err) {
        this.logger?.error(
          `usb: device.selectConfiguration error ${err}. device: ${this.formatDeviceForLog(device)}`
        );
      }
      try {
        this.logger?.debug("usb: device.reset");
        await this.abortableMethod(() => device?.reset(), { signal });
        this.logger?.debug(
          `usb: device.reset done. device: ${this.formatDeviceForLog(device)}`
        );
      } catch (err) {
        this.logger?.error(
          `usb: device.reset error ${err}. device: ${this.formatDeviceForLog(device)}`
        );
      }
    }
    try {
      const interfaceId = this.debugLink ? DEBUGLINK_INTERFACE_ID : INTERFACE_ID;
      this.logger?.debug(`usb: device.claimInterface: ${interfaceId}`);
      await this.abortableMethod(() => device.claimInterface(interfaceId), { signal });
      this.logger?.debug(
        `usb: device.claimInterface done: ${interfaceId}. device: ${this.formatDeviceForLog(device)}`
      );
    } catch (err) {
      this.logger?.error(
        `usb: device.claimInterface error ${err}. device: ${this.formatDeviceForLog(device)}`
      );
      return this.error({
        error: INTERFACE_UNABLE_TO_OPEN_DEVICE,
        message: err.message
      });
    }
    return this.success(void 0);
  }
  async closeDevice(path2) {
    const device = this.findDevice(path2);
    if (!device) {
      return this.error({ error: DEVICE_NOT_FOUND });
    }
    this.logger?.debug(`usb: closeDevice. device.opened: ${device.opened}`);
    if (device.opened) {
      try {
        const interfaceId = this.debugLink ? DEBUGLINK_INTERFACE_ID : INTERFACE_ID;
        this.logger?.debug(`usb: device.releaseInterface: ${interfaceId}`);
        if (!this.debugLink) {
          await device.reset();
        }
        await device.releaseInterface(interfaceId);
        this.logger?.debug(
          `usb: device.releaseInterface done: ${interfaceId}. device: ${this.formatDeviceForLog(device)}`
        );
      } catch (err) {
        this.logger?.error(
          `usb: releaseInterface error ${err}. device: ${this.formatDeviceForLog(device)}`
        );
      }
    }
    if (device.opened) {
      try {
        this.logger?.debug(`usb: device.close`);
        await device.close();
        this.logger?.debug(
          `usb: device.close done. device: ${this.formatDeviceForLog(device)}`
        );
      } catch (err) {
        this.logger?.debug(
          `usb: device.close error ${err}. device: ${this.formatDeviceForLog(device)}`
        );
        return this.error({
          error: INTERFACE_UNABLE_TO_CLOSE_DEVICE,
          message: err.message
        });
      }
    }
    return this.success(void 0);
  }
  findDevice(path2) {
    const device = this.devices.find((d) => d.path === path2);
    if (!device) {
      return;
    }
    return device.device;
  }
  async createDevices(devices, signal) {
    let bootloaderId = 0;
    const getPathFromUsbDevice = (device) => {
      const { serialNumber } = device;
      let path2 = serialNumber == null || serialNumber === "" ? "bootloader" : serialNumber;
      if (path2 === "bootloader") {
        this.logger?.debug("usb: device without serial number!");
        bootloaderId++;
        path2 += bootloaderId;
      }
      return path2;
    };
    const [hidDevices, nonHidDevices] = this.filterDevices(devices);
    hidDevices.forEach((device) => {
      this.logger?.error(
        `usb: unreadable hid device connected. device: ${this.formatDeviceForLog(device)}`
      );
    });
    const loadedDevices = await Promise.all(
      nonHidDevices.map(async (device) => {
        this.logger?.debug(`usb: creating device ${this.formatDeviceForLog(device)}`);
        if (this.forceReadSerialOnConnect && // device already has serialNumber or it is open - both cases mean that we already seen it before and don't need to bother
        !device.opened && !device.serialNumber) {
          await this.loadSerialNumber(device, signal);
        }
        const path2 = getPathFromUsbDevice(device);
        return { path: path2, device };
      })
    );
    return [
      ...loadedDevices,
      ...hidDevices.map((d) => ({
        path: getPathFromUsbDevice(d),
        device: d
      }))
    ];
  }
  /*
   * depending on OS (and specific usb drivers), it might be required to open device in order to read serial number.
   * https://github.com/node-usb/node-usb/issues/546
   */
  async loadSerialNumber(device, signal) {
    try {
      this.logger?.debug(`usb: loadSerialNumber`);
      await this.abortableMethod(() => device.open(), { signal });
      await this.abortableMethod(
        () => device.getStringDescriptor(device.device.deviceDescriptor.iSerialNumber),
        { signal }
      );
      this.logger?.debug(`usb: loadSerialNumber done, serialNumber: ${device.serialNumber}`);
      await this.abortableMethod(() => device.close(), { signal });
    } catch (err) {
      this.logger?.error(`usb: loadSerialNumber error: ${err.message}`);
      throw err;
    }
  }
  deviceIsHid(device) {
    return device.vendorId === T1_HID_VENDOR;
  }
  filterDevices(devices) {
    const trezorDevices = devices.filter((dev) => {
      const isTrezor = TREZOR_USB_DESCRIPTORS.some(
        (desc) => dev.vendorId === desc.vendorId && dev.productId === desc.productId
      );
      return isTrezor;
    });
    const hidDevices = trezorDevices.filter((dev) => this.deviceIsHid(dev));
    const nonHidDevices = trezorDevices.filter((dev) => !this.deviceIsHid(dev));
    return [hidDevices, nonHidDevices];
  }
  dispose() {
    if (this.usbInterface) {
      this.usbInterface.onconnect = null;
      this.usbInterface.ondisconnect = null;
    }
    this.abortController.abort();
  }
};

// ../transport/src/api/udp.ts
var import_dgram = __toESM(require("dgram"));
var UdpApi = class extends AbstractApi {
  chunkSize = 64;
  devices = [];
  interface = import_dgram.default.createSocket("udp4");
  communicating = false;
  enumerateAbortController = new AbortController();
  debugLink;
  constructor({ logger, debugLink }) {
    super({ logger });
    this.debugLink = debugLink;
  }
  listen() {
    if (this.listening) return;
    this.listening = true;
    this.listenLoop();
  }
  async listenLoop() {
    while (this.listening) {
      await createTimeoutPromise(500);
      if (!this.listening) break;
      await this.enumerate(this.enumerateAbortController.signal);
    }
  }
  write(path2, buffer, signal) {
    const [hostname, port] = path2.split(":");
    return new Promise((resolve) => {
      const listener = () => {
        resolve(
          this.error({
            error: ABORTED_BY_SIGNAL
          })
        );
      };
      signal?.addEventListener("abort", listener);
      this.interface.send(buffer, Number.parseInt(port, 10), hostname, (err) => {
        signal?.removeEventListener("abort", listener);
        if (signal?.aborted) {
          return;
        }
        if (err) {
          this.logger?.error(err.message);
          resolve(
            this.error({
              error: INTERFACE_DATA_TRANSFER,
              message: err.message
            })
          );
        }
        resolve(this.success(void 0));
      });
    });
  }
  read(_path, signal) {
    this.communicating = true;
    return new Promise((resolve) => {
      const onClear = () => {
        this.interface.removeListener("error", onError);
        this.interface.removeListener("message", onMessage);
        signal?.removeEventListener("abort", onAbort);
      };
      const onError = (err) => {
        this.logger?.error(err.message);
        resolve(
          this.error({
            error: INTERFACE_DATA_TRANSFER,
            message: err.message
          })
        );
        onClear();
      };
      const onMessage = (message, _info) => {
        if (message.toString() === "PONGPONG") {
          return;
        }
        onClear();
        resolve(this.success(message));
      };
      const onAbort = () => {
        onClear();
        return resolve(
          this.error({
            error: ABORTED_BY_SIGNAL
          })
        );
      };
      signal?.addEventListener("abort", onAbort);
      this.interface.addListener("error", onError);
      this.interface.addListener("message", onMessage);
    }).finally(() => {
      this.communicating = false;
    });
  }
  async ping(path2, signal) {
    await this.write(path2, Buffer.from("PINGPING"), signal);
    if (signal?.aborted) {
      throw new Error(ABORTED_BY_SIGNAL);
    }
    const pinged = new Promise((resolve) => {
      const onClear = () => {
        this.interface.removeListener("error", onError);
        this.interface.removeListener("message", onMessage);
        clearTimeout(timeout);
        signal?.removeEventListener("abort", onError);
      };
      const onError = () => {
        resolve(false);
        onClear();
      };
      const onMessage = (message, _info) => {
        if (message.toString() === "PONGPONG") {
          resolve(true);
          onClear();
        }
      };
      signal?.addEventListener("abort", onError);
      this.interface.addListener("error", onError);
      this.interface.addListener("message", onMessage);
      const timeout = setTimeout(onError, this.communicating ? 1e4 : 500);
    });
    return pinged;
  }
  async enumerate(signal) {
    const paths = this.debugLink ? ["127.0.0.1:21325"] : ["127.0.0.1:21324"];
    try {
      const enumerateResult = await Promise.all(
        paths.map(
          (path2) => this.ping(path2, signal).then(
            (pinged) => pinged ? { path: path2, type: 5 /* TypeEmulator */, product: 0, vendor: 0 } : void 0
          )
        )
      ).then((res) => res.filter(isNotUndefined));
      this.handleDevicesChange(enumerateResult);
      return this.success(enumerateResult);
    } catch (e) {
      this.handleDevicesChange([]);
      return this.error({ error: ABORTED_BY_SIGNAL });
    }
  }
  handleDevicesChange(devices) {
    const [known, unknown] = arrayPartition(devices, (device) => this.devices.includes(device));
    if (known.length !== this.devices.length || unknown.length > 0) {
      this.devices = devices;
      if (this.listening) {
        this.emit("transport-interface-change", this.devices);
      }
    }
  }
  openDevice(_path, _first, _signal) {
    return Promise.resolve(this.success(void 0));
  }
  closeDevice(_path) {
    return Promise.resolve(this.success(void 0));
  }
  dispose() {
    this.interface.removeAllListeners();
    this.interface.close();
    this.listening = false;
    this.enumerateAbortController.abort();
  }
};

// src/core.ts
var createCore = (apiArg, logger) => {
  let api;
  const sessionsBackground = new SessionsBackground();
  const sessionsClient = new SessionsClient({
    requestFn: (args) => sessionsBackground.handleMessage(args),
    registerBackgroundCallbacks: () => {
    }
  });
  sessionsBackground.on("descriptors", (descriptors) => {
    sessionsClient.emit("descriptors", descriptors);
  });
  if (typeof apiArg === "string") {
    api = apiArg === "udp" ? new UdpApi({ logger }) : new UsbApi({
      logger,
      usbInterface: new import_usb.WebUSB({
        allowAllDevices: true
        // return all devices, not only authorized
      }),
      // todo: possibly only for windows
      forceReadSerialOnConnect: true
    });
  } else {
    api = apiArg;
  }
  api.listen();
  api.on("transport-interface-change", (descriptors) => {
    logger?.debug(`core: transport-interface-change ${JSON.stringify(descriptors)}`);
    sessionsClient.enumerateDone({ descriptors });
  });
  const writeUtil = async ({
    path: path2,
    data,
    signal,
    protocol
  }) => {
    logger?.debug(`core: writeUtil protocol ${protocol.name}`);
    const buffer = Buffer.from(data, "hex");
    let encodedMessage;
    let chunkHeader;
    if (protocol.name === "bridge") {
      const { messageType, payload } = protocol_bridge_exports.decode(buffer);
      encodedMessage = protocol_v1_exports.encode(payload, { messageType });
      chunkHeader = protocol_v1_exports.getChunkHeader(encodedMessage);
    } else {
      encodedMessage = buffer;
      chunkHeader = protocol.getChunkHeader(encodedMessage);
    }
    const chunks = createChunks(encodedMessage, chunkHeader, api.chunkSize);
    const apiWrite = (chunk) => api.write(path2, chunk, signal);
    const sendResult = await sendChunks(chunks, apiWrite);
    return sendResult;
  };
  const readUtil = async ({
    path: path2,
    signal,
    protocol
  }) => {
    logger?.debug(`core: readUtil protocol ${protocol.name}`);
    try {
      const receiveProtocol = protocol.name === "bridge" ? protocol_v1_exports : protocol;
      const res = await receive(() => api.read(path2, signal), receiveProtocol);
      if (!res.success) return res;
      const { messageType, payload } = res.payload;
      logger?.debug(
        `core: readUtil result: messageType: ${messageType} byteLength: ${payload?.byteLength}`
      );
      return success(protocol.encode(payload, { messageType }).toString("hex"));
    } catch (err) {
      logger?.debug(`core: readUtil catch: ${err.message}`);
      return unknownError(err);
    }
  };
  const enumerate = async ({ signal }) => {
    const enumerateResult = await api.enumerate(signal);
    if (!enumerateResult.success) {
      return enumerateResult;
    }
    const enumerateDoneResponse = await sessionsClient.enumerateDone({
      descriptors: enumerateResult.payload
    });
    return enumerateDoneResponse;
  };
  const acquire = async (acquireInput) => {
    const acquireIntentResult = await sessionsClient.acquireIntent({
      path: acquireInput.path,
      previous: acquireInput.previous === "null" ? null : acquireInput.previous
    });
    if (!acquireIntentResult.success) {
      return acquireIntentResult;
    }
    const openDeviceResult = await api.openDevice(
      acquireIntentResult.payload.path,
      true,
      acquireInput.signal
    );
    logger?.debug(`core: openDevice: result: ${JSON.stringify(openDeviceResult)}`);
    if (!openDeviceResult.success) {
      return openDeviceResult;
    }
    await sessionsClient.acquireDone({ path: acquireInput.path });
    return acquireIntentResult;
  };
  const release = async ({ session }) => {
    await sessionsClient.releaseIntent({ session });
    const sessionsResult = await sessionsClient.getPathBySession({
      session
    });
    if (!sessionsResult.success) {
      return sessionsResult;
    }
    const closeRes = await api.closeDevice(sessionsResult.payload.path);
    if (!closeRes.success) {
      logger?.error(`core: release: api.closeDevice error: ${closeRes.error}`);
    }
    return sessionsClient.releaseDone({ path: sessionsResult.payload.path });
  };
  const getProtocol = (protocolName) => {
    if (protocolName === "v1") {
      return protocol_v1_exports;
    }
    return protocol_bridge_exports;
  };
  const createProtocolMessageResponse = (response, protocolName) => {
    if (response.success) {
      const body = "payload" in response ? response.payload : "";
      return {
        ...response,
        payload: createProtocolMessage(body, protocolName)
      };
    }
    return response;
  };
  const call = async ({
    session,
    data,
    signal,
    protocol: protocolName
  }) => {
    logger?.debug(`core: call: session: ${session}`);
    const sessionsResult = await sessionsClient.getPathBySession({
      session
    });
    if (!sessionsResult.success) {
      logger?.error(`core: call: retrieving path error: ${sessionsResult.error}`);
      return sessionsResult;
    }
    const protocol = getProtocol(protocolName);
    const { path: path2 } = sessionsResult.payload;
    logger?.debug(`core: call: retrieved path ${path2} for session ${session}`);
    return api.runInIsolation({ lock: { read: true, write: true }, path: path2 }, async () => {
      const openResult = await api.openDevice(path2, false, signal);
      if (!openResult.success) {
        logger?.error(`core: call: api.openDevice error: ${openResult.error}`);
        return openResult;
      }
      logger?.debug(`core: call: api.openDevice done`);
      logger?.debug("core: call: writeUtil");
      const writeResult = await writeUtil({ path: path2, data, signal, protocol });
      if (!writeResult.success) {
        logger?.error(`core: call: writeUtil ${writeResult.error}`);
        return writeResult;
      }
      logger?.debug("core: call: readUtil");
      const readResult = await readUtil({ path: path2, signal, protocol });
      return createProtocolMessageResponse(readResult, protocolName);
    });
  };
  const send = async ({
    session,
    data,
    signal,
    protocol: protocolName
  }) => {
    const sessionsResult = await sessionsClient.getPathBySession({
      session
    });
    if (!sessionsResult.success) {
      return sessionsResult;
    }
    const protocol = getProtocol(protocolName);
    const { path: path2 } = sessionsResult.payload;
    const openResult = await api.openDevice(path2, false, signal);
    if (!openResult.success) {
      return openResult;
    }
    const writeResult = await writeUtil({ path: path2, data, signal, protocol });
    return createProtocolMessageResponse(writeResult, protocolName);
  };
  const receive2 = async ({
    session,
    signal,
    protocol: protocolName
  }) => {
    const sessionsResult = await sessionsClient.getPathBySession({
      session
    });
    if (!sessionsResult.success) {
      return sessionsResult;
    }
    const protocol = getProtocol(protocolName);
    const { path: path2 } = sessionsResult.payload;
    return api.runInIsolation({ lock: { read: true, write: false }, path: path2 }, async () => {
      const openResult = await api.openDevice(path2, false, signal);
      if (!openResult.success) {
        return openResult;
      }
      const readResult = await readUtil({ path: path2, signal, protocol });
      return createProtocolMessageResponse(readResult, protocolName);
    });
  };
  const dispose = () => {
    sessionsBackground.dispose();
    api.dispose();
    sessionsClient.dispose();
  };
  return {
    enumerate,
    acquire,
    release,
    call,
    send,
    receive: receive2,
    dispose,
    sessionsClient
  };
};

// src/http.ts
var defaults = {
  port: 21325
};
var str = (value) => typeof value === "string" ? value : JSON.stringify(value);
var validateDescriptorsJSON = (request, response, next) => {
  if (Array.isArray(request.body)) {
    next({ ...request, body: request.body }, response);
  } else {
    response.statusCode = 400;
    response.end(str({ error: "Invalid body" }));
  }
};
var validateAcquireParams = (request, response, next) => {
  if (typeof request.params.path === "string" && /^[1-9][0-9]*$/.test(request.params.path) && typeof request.params.previous === "string" && /^\d+$|^null$/.test(request.params.previous)) {
    next(request, response);
  } else {
    response.statusCode = 400;
    response.end(str({ error: "Invalid params" }));
  }
};
var validateSessionParams = (request, response, next) => {
  if (typeof request.params.session === "string" && /^\d+$/.test(request.params.session)) {
    next(request, response);
  } else {
    response.statusCode = 400;
    response.end(str({ error: "Invalid params" }));
  }
};
var validateProtocolMessageBody = (withData, protocolMessages) => (request, response, next) => {
  try {
    const body = validateProtocolMessage(request.body, withData);
    if (!protocolMessages && body.protocol) {
      throw new Error("BridgeProtocolMessage support is disabled");
    }
    return next({ ...request, body }, response);
  } catch (error2) {
    response.statusCode = 400;
    response.end(str({ error: error2.message }));
  }
};
var TrezordNode = class {
  /** versioning, baked in by webpack */
  version = "3.0.0";
  serviceName = "trezord-node";
  /** last known descriptors state */
  descriptors;
  /** pending /listen subscriptions that are supposed to be resolved whenever descriptors change is detected */
  listenSubscriptions;
  port;
  server;
  core;
  logger;
  assetPrefix;
  protocolMessages;
  throttler = new Throttler(500);
  constructor({
    port,
    api,
    assetPrefix = "",
    logger,
    protocolMessages,
    bundledVersion
  }) {
    this.port = port || defaults.port;
    this.logger = logger;
    this.descriptors = [];
    if (bundledVersion) {
      this.version = `${this.version}-bundled.${bundledVersion}`;
    }
    this.listenSubscriptions = [];
    this.core = createCore(api, this.logger);
    this.assetPrefix = assetPrefix;
    this.protocolMessages = protocolMessages ?? true;
  }
  checkAffectedSubscriptions() {
    const [aborted, notAborted] = arrayPartition(this.listenSubscriptions, (subscription) => {
      return subscription.res.destroyed;
    });
    if (aborted.length) {
      this.logger?.debug(
        `http: resolving listen subscriptions. n of aborted subscriptions: ${aborted.length}`
      );
    }
    const [affected, unaffected] = arrayPartition(notAborted, (subscription) => {
      return (0, import_json_stable_stringify.default)(subscription.descriptors) !== (0, import_json_stable_stringify.default)(this.descriptors);
    });
    this.logger?.debug(
      `http: affected subscriptions ${affected.length}. unaffected subscriptions ${unaffected.length}`
    );
    affected.forEach((subscription) => {
      subscription.res.end(str(this.descriptors));
    });
    this.listenSubscriptions = unaffected;
  }
  resolveListenSubscriptions(nextDescriptors) {
    this.descriptors = nextDescriptors;
    if (!this.listenSubscriptions.length) {
      return;
    }
    this.checkAffectedSubscriptions();
  }
  createAbortSignal(res) {
    const abortController = new AbortController();
    const listener = () => {
      abortController.abort();
      res.removeListener("close", listener);
    };
    res.addListener("close", listener);
    return abortController.signal;
  }
  handleInfo(_req, res) {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(
      str({
        version: this.version,
        protocolMessages: this.protocolMessages
      })
    );
  }
  start() {
    this.core.sessionsClient.on("descriptors", (descriptors) => {
      this.logger?.debug(
        `http: sessionsClient reported descriptors: ${JSON.stringify(descriptors)}`
      );
      this.throttler.throttle("resolve-listen-subscriptions", () => {
        return this.resolveListenSubscriptions(descriptors);
      });
    });
    return new Promise((resolve, reject) => {
      this.logger.info("Starting Trezor Bridge HTTP server");
      const app = new HttpServer({
        port: this.port,
        logger: this.logger
      });
      app.use([
        (req, res, next, context) => {
          if (!req.headers.origin && req.headers.host && [`127.0.0.1:${this.port}`, `localhost:${this.port}`].includes(
            req.headers.host
          )) {
            next(req, res);
          } else {
            allowOrigins([
              "https://sldev.cz",
              "https://trezor.io",
              "http://localhost",
              // When using Tor it will send string "null" as default, and it will not allow calling to localhost.
              // To allow it to be sent, you can go to about:config and set the attributes below:
              // "network.http.referer.hideOnionSource - false"
              // "network.proxy.allow_hijacking_localhost - false"
              "http://suite.trezoriovpjcahpzkrewelclulmszwbqpzmzgub37gbcjlvluxtruqad.onion"
            ])(req, res, next, context);
          }
        }
      ]);
      app.use([
        (req, res, next) => {
          if (req.headers.origin) {
            res.setHeader("Access-Control-Allow-Origin", req.headers.origin);
          }
          next(req, res);
        }
      ]);
      app.post("/enumerate", [
        (_req, res) => {
          res.setHeader("Content-Type", "text/plain");
          const signal = this.createAbortSignal(res);
          this.core.enumerate({ signal }).then((result) => {
            if (!result.success) {
              res.statusCode = 400;
              return res.end(str({ error: result.error }));
            }
            res.end(str(result.payload.descriptors));
          });
        }
      ]);
      app.post("/listen", [
        parseBodyJSON,
        validateDescriptorsJSON,
        (req, res) => {
          res.setHeader("Content-Type", "text/plain");
          this.listenSubscriptions.push({
            descriptors: req.body,
            req,
            res
          });
          this.checkAffectedSubscriptions();
        }
      ]);
      app.post("/acquire/:path/:previous", [
        validateAcquireParams,
        (req, res) => {
          res.setHeader("Content-Type", "text/plain");
          const signal = this.createAbortSignal(res);
          this.core.acquire({
            path: req.params.path,
            previous: req.params.previous,
            signal
          }).then((result) => {
            if (!result.success) {
              res.statusCode = 400;
              return res.end(str({ error: result.error }));
            }
            res.end(str({ session: result.payload.session }));
          });
        }
      ]);
      app.post("/release/:session", [
        validateSessionParams,
        parseBodyText,
        (req, res) => {
          this.core.release({
            session: req.params.session
          }).then((result) => {
            if (!result.success) {
              res.statusCode = 400;
              return res.end(str({ error: result.error }));
            }
            res.end(str({ session: req.params.session }));
          });
        }
      ]);
      app.post("/call/:session", [
        validateSessionParams,
        parseBodyText,
        validateProtocolMessageBody(true, this.protocolMessages),
        (req, res) => {
          const signal = this.createAbortSignal(res);
          this.core.call({
            ...req.body,
            session: req.params.session,
            signal
          }).then((result) => {
            if (!result.success) {
              res.statusCode = 400;
              return res.end(str({ error: result.error }));
            }
            res.end(str(result.payload));
          });
        }
      ]);
      app.post("/read/:session", [
        validateSessionParams,
        parseBodyText,
        validateProtocolMessageBody(false, this.protocolMessages),
        (req, res) => {
          const signal = this.createAbortSignal(res);
          this.core.receive({
            ...req.body,
            session: req.params.session,
            signal
          }).then((result) => {
            if (!result.success) {
              res.statusCode = 400;
              return res.end(str({ error: result.error }));
            }
            res.end(str(result.payload));
          });
        }
      ]);
      app.post("/post/:session", [
        validateSessionParams,
        parseBodyText,
        validateProtocolMessageBody(true, this.protocolMessages),
        (req, res) => {
          const signal = this.createAbortSignal(res);
          this.core.send({
            ...req.body,
            session: req.params.session,
            signal
          }).then((result) => {
            if (!result.success) {
              res.statusCode = 400;
              return res.end(str({ error: result.error }));
            }
            res.end(str(result.payload));
          });
        }
      ]);
      app.get("/", [
        (_req, res) => {
          res.writeHead(301, {
            Location: `http://127.0.0.1:${this.port}/status`
          });
          res.end();
        }
      ]);
      app.get("/status", [
        async (_req, res) => {
          try {
            const ui = await import_promises.default.readFile(
              import_path.default.join(__dirname, this.assetPrefix, "ui/index.html"),
              "utf-8"
            );
            res.writeHead(200, { "Content-Type": "text/html" });
            res.end(ui);
          } catch (error2) {
            this.logger.error("Failed to fetch status page", error2);
            res.writeHead(200, { "Content-Type": "text/plain" });
            res.end("Failed to fetch status page");
          }
        }
      ]);
      app.get("/status-data", [
        (_req, res) => {
          const props = {
            intro: `To download full logs go to http://127.0.0.1:${this.port}/logs`,
            version: this.version,
            devices: this.descriptors,
            logs: this.logger.getLog()
          };
          res.end(str(props));
        }
      ]);
      app.get("/ui", [
        (req, res) => {
          const parsedUrl = new URL(req.url, `http://${req.headers.host}/`);
          let pathname = import_path.default.join(__dirname, this.assetPrefix, parsedUrl.pathname);
          const map = {
            ".ico": "image/x-icon",
            ".html": "text/html",
            ".js": "text/javascript",
            ".json": "application/json",
            ".css": "text/css",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml"
          };
          const { ext } = import_path.default.parse(pathname);
          import_promises.default.stat(pathname).then(() => import_promises.default.readFile(pathname)).then((data) => {
            res.setHeader("Content-type", map[ext] || "text/plain");
            res.end(data);
          }).catch((err) => {
            this.logger.error("Failed to fetch UI", err);
            res.statusCode = 404;
            res.end(`File ${pathname} not found!`);
          });
        }
      ]);
      app.get("/logs", [
        (_req, res) => {
          res.writeHead(200, {
            "Content-Type": "text/plain",
            "Content-Disposition": "attachment; filename=trezor-bridge.txt"
          });
          res.end(
            app.logger.getLog().map((l) => l.message.join(". ")).join(".\n")
          );
        }
      ]);
      app.post("/", [this.handleInfo.bind(this)]);
      app.post("/configure", [this.handleInfo.bind(this)]);
      app.start().then(() => {
        this.server = app;
        resolve();
      }).catch(reject);
    });
  }
  stop() {
    this.resolveListenSubscriptions([]);
    this.throttler.dispose();
    this.core.dispose();
    return this.server?.stop();
  }
  async status() {
    const running = await fetch(`http://127.0.0.1:${this.port}/`).then((resp) => resp.ok).catch(() => false);
    return {
      service: running,
      process: running
    };
  }
  // compatibility with "BridgeProcess" type
  startDev() {
    return this.start();
  }
  // compatibility with "BridgeProcess" type
  startTest() {
    return this.start();
  }
};

// src/bin.ts
var trezordNode = new TrezordNode({
  port: 21325,
  api: process.argv.includes("udp") ? "udp" : "usb",
  logger: new Log("@trezor/transport-bridge", true)
});
trezordNode.start();
