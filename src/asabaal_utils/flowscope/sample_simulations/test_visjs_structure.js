// Test vis.js structure without browser
const fs = require('fs');

// Read the vis.js library to understand its structure
const visJsPath = './lib/vis-network/vis-network.min.js';
if (fs.existsSync(visJsPath)) {
    const visJsContent = fs.readFileSync(visJsPath, 'utf8');
    console.log('vis.js file size:', visJsContent.length, 'characters');
    console.log('First 200 characters:', visJsContent.substring(0, 200));
} else {
    console.log('vis.js library not found at:', visJsPath);
}

// Let's create a simple test to understand what edges.get() should return
console.log('\n=== Expected vis.js DataSet behavior ===');
console.log('vis.DataSet should have methods:');
console.log('- get(): returns array of all items');
console.log('- get(id): returns specific item');
console.log('- add(): adds items');
console.log('- forEach(): iterates over items');

// Test what our edge data should look like
const testEdges = [
    {from: 'a', to: 'b'}
];

console.log('\n=== Test edge data structure ===');
console.log('Test edges:', JSON.stringify(testEdges, null, 2));
console.log('Edge 0 from:', testEdges[0].from);
console.log('Edge 0 to:', testEdges[0].to);

// Test what positions should look like
const testPositions = {
    'a': {x: 100, y: 100},
    'b': {x: 200, y: 150}
};

console.log('\n=== Test position data structure ===');
console.log('Test positions:', JSON.stringify(testPositions, null, 2));
console.log('Position A:', testPositions['a']);
console.log('Position B:', testPositions['b']);

// Test the edge processing logic
console.log('\n=== Test edge processing logic ===');
testEdges.forEach(edge => {
    const pos1 = testPositions[edge.from];
    const pos2 = testPositions[edge.to];
    console.log('Edge:', edge);
    console.log('  pos1:', pos1);
    console.log('  pos2:', pos2);
    
    if (pos1 && pos2) {
        const dx = pos2.x - pos1.x;
        const dy = pos2.y - pos1.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        console.log('  dx:', dx, 'dy:', dy, 'distance:', distance);
    } else {
        console.log('  ERROR: Missing positions!');
    }
});