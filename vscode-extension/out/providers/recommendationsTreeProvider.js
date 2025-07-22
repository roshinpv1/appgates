"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.RecommendationsTreeProvider = exports.RecommendationTreeItem = void 0;
const vscode = __importStar(require("vscode"));
class RecommendationTreeItem extends vscode.TreeItem {
    constructor(label, collapsibleState, recommendation, contextValue) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.recommendation = recommendation;
        this.contextValue = contextValue;
        if (recommendation) {
            this.tooltip = recommendation;
            this.iconPath = new vscode.ThemeIcon('lightbulb', new vscode.ThemeColor('editorLightBulb.foreground'));
            this.contextValue = 'recommendation';
        }
        else {
            this.iconPath = new vscode.ThemeIcon('list-unordered');
        }
    }
}
exports.RecommendationTreeItem = RecommendationTreeItem;
class RecommendationsTreeProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.scanResult = null;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    updateResults(result) {
        this.scanResult = result;
        this.refresh();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!this.scanResult) {
            return Promise.resolve([]);
        }
        if (!element) {
            // Root level - show categories
            const gateRecommendations = this.getGateRecommendations();
            const generalRecommendations = this.scanResult.recommendations || [];
            const categories = [];
            if (gateRecommendations.length > 0) {
                categories.push(new RecommendationTreeItem(`Gate-Specific (${gateRecommendations.length})`, vscode.TreeItemCollapsibleState.Expanded, undefined, 'category'));
            }
            const filteredGeneralRecommendations = generalRecommendations.filter(rec => !/Achieved:|Exceeds expectations|coverage/i.test(rec));
            if (filteredGeneralRecommendations.length > 0) {
                categories.push(new RecommendationTreeItem(`General (${filteredGeneralRecommendations.length})`, vscode.TreeItemCollapsibleState.Expanded, undefined, 'category'));
            }
            return Promise.resolve(categories);
        }
        // Show recommendations by category
        if (element.label.startsWith('Gate-Specific')) {
            const gateRecommendations = this.getGateRecommendations().filter(rec => !/Achieved:|Exceeds expectations|coverage/i.test(rec.recommendation));
            return Promise.resolve(gateRecommendations.map((rec, index) => new RecommendationTreeItem(`${rec.gate}: ${rec.recommendation.substring(0, 50)}${rec.recommendation.length > 50 ? '...' : ''}`, vscode.TreeItemCollapsibleState.None, rec.recommendation)));
        }
        else if (element.label.startsWith('General')) {
            const generalRecommendations = (this.scanResult.recommendations || []).filter(rec => !/Achieved:|Exceeds expectations|coverage/i.test(rec));
            return Promise.resolve(generalRecommendations.map((rec, index) => new RecommendationTreeItem(rec.length > 60 ? `${rec.substring(0, 60)}...` : rec, vscode.TreeItemCollapsibleState.None, rec)));
        }
        return Promise.resolve([]);
    }
    getGateRecommendations() {
        if (!this.scanResult || !this.scanResult.gate_scores) {
            return [];
        }
        const gateRecommendations = [];
        for (const gateScore of this.scanResult.gate_scores) {
            if (gateScore.recommendations && gateScore.recommendations.length > 0) {
                for (const recommendation of gateScore.recommendations) {
                    gateRecommendations.push({
                        gate: this.formatGateName(gateScore.gate),
                        recommendation
                    });
                }
            }
        }
        return gateRecommendations;
    }
    formatGateName(gateName) {
        return gateName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
}
exports.RecommendationsTreeProvider = RecommendationsTreeProvider;
//# sourceMappingURL=recommendationsTreeProvider.js.map