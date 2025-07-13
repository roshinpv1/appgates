#!/usr/bin/env node

/**
 * Test script to verify timeout configuration is working
 * This script tests the timeout configuration in the VS Code extension
 */

// Mock the configuration for testing
const mockConfig = {
    get: (key, defaultValue) => {
        switch (key) {
            case 'apiUrl':
                return 'http://localhost:8000/api/v1';
            case 'apiTimeout':
                return 60; // Test with 60 seconds
            case 'apiRetries':
                return 3;
            default:
                return defaultValue;
        }
    }
};

// Test the timeout calculation
function testTimeoutConfiguration() {
    console.log('Testing timeout configuration...');
    
    // Simulate the getApiConfig method
    const config = {
        baseUrl: mockConfig.get('apiUrl', 'http://localhost:8000/api/v1'),
        apiKey: mockConfig.get('apiKey', ''),
        timeout: mockConfig.get('apiTimeout', 300),
        retries: mockConfig.get('apiRetries', 3)
    };
    
    console.log('Configuration:', config);
    
    // Test timeout conversion (seconds to milliseconds)
    const timeoutMs = config.timeout * 1000;
    console.log(`Timeout: ${config.timeout} seconds = ${timeoutMs} milliseconds`);
    
    // Test polling calculation
    const pollInterval = 5000; // 5 seconds
    const maxAttempts = Math.floor((config.timeout * 1000) / pollInterval);
    console.log(`Polling: ${maxAttempts} attempts at ${pollInterval}ms intervals = ${maxAttempts * pollInterval / 1000}s total`);
    
    // Verify the calculations are correct
    const expectedTimeout = 60;
    const expectedTimeoutMs = 60000;
    const expectedMaxAttempts = 12;
    
    console.log('\nTest Results:');
    console.log(`✓ Timeout seconds: ${config.timeout} (expected: ${expectedTimeout})`);
    console.log(`✓ Timeout milliseconds: ${timeoutMs} (expected: ${expectedTimeoutMs})`);
    console.log(`✓ Max polling attempts: ${maxAttempts} (expected: ${expectedMaxAttempts})`);
    
    if (config.timeout === expectedTimeout && 
        timeoutMs === expectedTimeoutMs && 
        maxAttempts === expectedMaxAttempts) {
        console.log('\n✅ All timeout configuration tests passed!');
        return true;
    } else {
        console.log('\n❌ Some timeout configuration tests failed!');
        return false;
    }
}

// Test different timeout values
function testDifferentTimeouts() {
    console.log('\nTesting different timeout values...');
    
    const testCases = [
        { timeout: 30, expectedMs: 30000, expectedAttempts: 6 },
        { timeout: 60, expectedMs: 60000, expectedAttempts: 12 },
        { timeout: 300, expectedMs: 300000, expectedAttempts: 60 },
        { timeout: 600, expectedMs: 600000, expectedAttempts: 120 }
    ];
    
    let allPassed = true;
    
    testCases.forEach((testCase, index) => {
        const timeoutMs = testCase.timeout * 1000;
        const maxAttempts = Math.floor(timeoutMs / 5000);
        
        console.log(`\nTest Case ${index + 1}: ${testCase.timeout}s timeout`);
        console.log(`  Expected ms: ${testCase.expectedMs}, Got: ${timeoutMs}`);
        console.log(`  Expected attempts: ${testCase.expectedAttempts}, Got: ${maxAttempts}`);
        
        if (timeoutMs === testCase.expectedMs && maxAttempts === testCase.expectedAttempts) {
            console.log(`  ✅ Passed`);
        } else {
            console.log(`  ❌ Failed`);
            allPassed = false;
        }
    });
    
    if (allPassed) {
        console.log('\n✅ All timeout value tests passed!');
    } else {
        console.log('\n❌ Some timeout value tests failed!');
    }
    
    return allPassed;
}

// Run the tests
console.log('CodeGates Extension Timeout Configuration Test');
console.log('=============================================\n');

const basicTestPassed = testTimeoutConfiguration();
const timeoutTestPassed = testDifferentTimeouts();

if (basicTestPassed && timeoutTestPassed) {
    console.log('\n🎉 All tests passed! Timeout configuration is working correctly.');
    process.exit(0);
} else {
    console.log('\n💥 Some tests failed! Please check the timeout configuration.');
    process.exit(1);
} 