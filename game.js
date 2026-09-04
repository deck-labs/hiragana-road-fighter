const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score');
const fuelElement = document.getElementById('fuel');
const gameOverScreen = document.getElementById('game-over');
const gameOverTitle = document.getElementById('game-over-title');
const finalScoreElement = document.getElementById('final-score');
const restartBtn = document.getElementById('restart-btn');

// Game constants
const ROAD_WIDTH = 300;
const ROAD_MARGIN = (canvas.width - ROAD_WIDTH) / 2;
const CAR_WIDTH = 38;
const CAR_HEIGHT = 66;
const PLAYER_SPEED_X = 5;
const BASE_SCROLL_SPEED = 4;
const FUEL_DEPLETION_RATE = 0.06;
const FUEL_REWARD = 20;
const FUEL_PENALTY = 15;
const MAX_FUEL = 100;
const WIN_SCORE = 3000;

// Kana data (Stage 1)
const KANA_SET = [
    { kana: 'あ', romaji: 'a', color: '#3366ff' }, // Blue
    { kana: 'い', romaji: 'i', color: '#2ecc71' }, // Green
    { kana: 'う', romaji: 'u', color: '#f1c40f' }, // Yellow
    { kana: 'え', romaji: 'e', color: '#9b59b6' }, // Purple
    { kana: 'お', romaji: 'o', color: '#e67e22' }  // Orange
];

// Game state
let player = {
    x: canvas.width / 2 - CAR_WIDTH / 2,
    y: canvas.height - CAR_HEIGHT - 30,
    width: CAR_WIDTH,
    height: CAR_HEIGHT,
    color: '#ff3333',
    targetKana: null,
    isSpinning: false,
    spinAngle: 0
};

let enemies = [];
let roadOffset = 0;
let score = 0;
let fuel = MAX_FUEL;
let gameRunning = false;
let keys = { ArrowLeft: false, ArrowRight: false, ArrowUp: false, ArrowDown: false };
let speedMultiplier = 1;
let frames = 0;

function getRandomKana() {
    return KANA_SET[Math.floor(Math.random() * KANA_SET.length)];
}

function spawnEnemy() {
    const laneWidth = ROAD_WIDTH / 4;
    const availableLanes = [];
    for (let lane = 0; lane < 4; lane++) {
        const lx = ROAD_MARGIN + lane * laneWidth + (laneWidth - CAR_WIDTH) / 2;
        let laneClear = true;
        for (let e of enemies) {
            if (Math.abs(e.x - lx) < laneWidth - 5 && e.y < CAR_HEIGHT * 2.5) {
                laneClear = false;
                break;
            }
        }
        if (laneClear) {
            availableLanes.push(lx);
        }
    }
    
    if (availableLanes.length === 0) return;
    const x = availableLanes[Math.floor(Math.random() * availableLanes.length)];
    
    // Give player a fair chance at correct answer
    let kanaData;
    if (Math.random() > 0.4) {
        kanaData = player.targetKana; // 60% chance to spawn the correct answer
    } else {
        kanaData = getRandomKana(); // 40% chance to spawn random
    }
    
    // Enemy speed determines how fast they move down the road independently.
    // 1 is slow (player overtakes easily), 3 is fast (player still overtakes if moving normal speed).
    let speed = 1.5 + Math.random() * 1.5; 
    
    enemies.push({
        x: x,
        y: -CAR_HEIGHT,
        width: CAR_WIDTH,
        height: CAR_HEIGHT,
        color: kanaData.color,
        speed: speed,
        data: kanaData
    });
}

function init() {
    player.x = canvas.width / 2 - CAR_WIDTH / 2;
    player.targetKana = getRandomKana();
    player.isSpinning = false;
    player.spinAngle = 0;
    player.color = '#ff3333';
    
    enemies = [];
    score = 0;
    fuel = MAX_FUEL;
    roadOffset = 0;
    gameRunning = true;
    speedMultiplier = 1;
    frames = 0;
    
    gameOverScreen.classList.add('hidden');
    updateUI();
    requestAnimationFrame(gameLoop);
}

function updateUI() {
    scoreElement.innerText = Math.floor(score);
    fuelElement.value = fuel;
}

function handleInput() {
    if (player.isSpinning) return;
    
    if (keys.ArrowLeft && player.x > ROAD_MARGIN) {
        player.x -= PLAYER_SPEED_X;
    }
    if (keys.ArrowRight && player.x < canvas.width - ROAD_MARGIN - CAR_WIDTH) {
        player.x += PLAYER_SPEED_X;
    }
    
    if (keys.ArrowUp) {
        speedMultiplier = 1.5; // Accelerate
    } else if (keys.ArrowDown) {
        speedMultiplier = 0.5; // Brake
    } else {
        speedMultiplier = 1; // Normal speed
    }
}

function drawTree(x, y) {
    // Trunk
    ctx.fillStyle = '#5f3714';
    ctx.fillRect(x - 2, y + 4, 5, 12);
    // Foliage layers
    ctx.fillStyle = '#125a16';
    ctx.beginPath(); ctx.arc(x, y + 2, 11, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#229126';
    ctx.beginPath(); ctx.arc(x, y - 3, 9, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#3ac33e';
    ctx.beginPath(); ctx.arc(x - 2, y - 5, 6, 0, Math.PI * 2); ctx.fill();
}

function drawFinishLine(y) {
    const squareSize = 15;
    const numCols = Math.floor(ROAD_WIDTH / squareSize);
    const numRows = 2;

    // Checkered pattern
    for (let row = 0; row < numRows; row++) {
        for (let col = 0; col < numCols; col++) {
            ctx.fillStyle = (row + col) % 2 === 0 ? '#111' : '#eee';
            ctx.fillRect(ROAD_MARGIN + col * squareSize, y + row * squareSize, squareSize, squareSize);
        }
    }

    // Goal posts
    for (let sideX of [ROAD_MARGIN - 14, ROAD_MARGIN + ROAD_WIDTH + 2]) {
        for (let r = 0; r < 4; r++) {
            ctx.fillStyle = r % 2 === 0 ? '#e74c3c' : '#ffffff';
            ctx.fillRect(sideX, y - 8 + r * 10, 12, 10);
            ctx.strokeStyle = '#000';
            ctx.strokeRect(sideX, y - 8 + r * 10, 12, 10);
        }
    }

    // Overhead GOAL banner
    ctx.save();
    ctx.font = 'bold 16px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const text = '★ GOAL ★';
    const tw = ctx.measureText(text).width;
    const bx = ROAD_MARGIN + ROAD_WIDTH / 2;
    const by = y - 20;

    ctx.fillStyle = '#000000';
    ctx.fillRect(bx - tw / 2 - 8, by - 12, tw + 16, 24);
    ctx.strokeStyle = '#ffeb3b';
    ctx.lineWidth = 2;
    ctx.strokeRect(bx - tw / 2 - 8, by - 12, tw + 16, 24);

    ctx.fillStyle = '#ffeb3b';
    ctx.fillText(text, bx, by);
    ctx.restore();
}

function drawRoad() {
    // Grass
    ctx.fillStyle = '#1e751e';
    ctx.fillRect(0, 0, ROAD_MARGIN, canvas.height);
    ctx.fillRect(canvas.width - ROAD_MARGIN, 0, ROAD_MARGIN, canvas.height);
    
    // Grass details (moving)
    ctx.fillStyle = '#268c26';
    for (let i = 0; i < 10; i++) {
        let y = ((i * 100) + roadOffset) % canvas.height;
        ctx.fillRect(8, y, 16, 16);
        ctx.fillRect(canvas.width - 24, y + 50, 16, 16);
    }

    // Roadside trees
    for (let i = -2; i < 7; i++) {
        let y = ((i * 130) + roadOffset) % (canvas.height + 130) - 65;
        drawTree(10, y);
    }
    for (let i = -2; i < 9; i++) {
        let y = ((i * 85) + roadOffset) % (canvas.height + 85) - 40;
        let tx = 375 + (i % 2 === 0 ? 8 : -8);
        drawTree(tx, y);
    }
    
    // Road surface
    ctx.fillStyle = '#555';
    ctx.fillRect(ROAD_MARGIN, 0, ROAD_WIDTH, canvas.height);
    
    // Center lines
    ctx.fillStyle = '#fff';
    for (let i = -100; i < canvas.height; i += 60) {
        let y = (i + roadOffset) % (canvas.height + 60) - 60;
        ctx.fillRect(ROAD_MARGIN + ROAD_WIDTH / 2 - 2, y, 4, 30);
    }
    
    // Edge lines
    ctx.fillStyle = '#ccc';
    ctx.fillRect(ROAD_MARGIN, 0, 4, canvas.height);
    ctx.fillRect(ROAD_MARGIN + ROAD_WIDTH - 4, 0, 4, canvas.height);

    // Finish Line
    const distanceToFinish = (WIN_SCORE - score) * 10;
    const finishLineY = player.y - distanceToFinish;
    if (finishLineY >= -80 && finishLineY <= canvas.height + 80) {
        drawFinishLine(finishLineY);
    }
}

function drawCar(car, isPlayer) {
    ctx.save();
    
    let drawX = car.x;
    let drawY = car.y;
    
    if (isPlayer && car.isSpinning) {
        // Spin animation
        ctx.translate(car.x + car.width/2, car.y + car.height/2);
        ctx.rotate(car.spinAngle);
        drawX = -car.width/2;
        drawY = -car.height/2;
    }
    
    // Shadow
    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    ctx.fillRect(drawX + 4, drawY + 4, car.width, car.height);
    
    // Main body
    ctx.fillStyle = car.color;
    ctx.fillRect(drawX, drawY, car.width, car.height);
    
    // Solid opaque roof (dark solid overlay)
    ctx.fillStyle = '#1a1a24';
    ctx.fillRect(drawX + 4, drawY + 13, car.width - 8, car.height - 26);
    
    // Windshield
    ctx.fillStyle = '#88ccff';
    ctx.fillRect(drawX + 4, drawY + 4, car.width - 8, 7);
    
    // Rear window
    ctx.fillStyle = '#225588';
    ctx.fillRect(drawX + 4, drawY + car.height - 11, car.width - 8, 7);
    
    // Wheels
    ctx.fillStyle = '#111';
    ctx.fillRect(drawX - 2, drawY + 8, 4, 14);
    ctx.fillRect(drawX + car.width - 2, drawY + 8, 4, 14);
    ctx.fillRect(drawX - 2, drawY + car.height - 22, 4, 14);
    ctx.fillRect(drawX + car.width - 2, drawY + car.height - 22, 4, 14);
    
    // Text
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 24px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // Text shadow for readability
    ctx.shadowColor = 'black';
    ctx.shadowBlur = 4;
    ctx.shadowOffsetX = 1;
    ctx.shadowOffsetY = 1;
    
    if (isPlayer) {
        ctx.fillText(car.targetKana.kana, drawX + car.width / 2, drawY + car.height / 2);
    } else {
        ctx.fillText(car.data.romaji, drawX + car.width / 2, drawY + car.height / 2);
    }
    
    ctx.restore();
}

function checkCollision(rect1, rect2) {
    return rect1.x < rect2.x + rect2.width - 5 &&
           rect1.x + rect1.width > rect2.x + 5 &&
           rect1.y < rect2.y + rect2.height - 5 &&
           rect1.y + rect1.height > rect2.y + 5; // -5 for slight leniency
}

function spinOut() {
    if (player.isSpinning) return;
    player.isSpinning = true;
    player.color = '#777'; // Gray out
    
    let spinDuration = 60; // frames
    let currentFrame = 0;
    
    function spinAnimation() {
        if (!gameRunning) return;
        currentFrame++;
        player.spinAngle += 0.3; // rotate
        
        if (currentFrame < spinDuration) {
            requestAnimationFrame(spinAnimation);
        } else {
            player.isSpinning = false;
            player.spinAngle = 0;
            player.color = '#ff3333';
        }
    }
    spinAnimation();
}

function gameOver(won = false) {
    gameRunning = false;
    finalScoreElement.innerText = Math.floor(score);
    if (won) {
        gameOverTitle.innerText = "STAGE CLEAR!";
        gameOverTitle.style.color = "#ffeb3b";
    } else {
        gameOverTitle.innerText = "OUT OF GAS!";
        gameOverTitle.style.color = "#f00";
    }
    gameOverScreen.classList.remove('hidden');
}

function update() {
    if (!gameRunning) return;
    
    frames++;
    handleInput();
    
    let scrollSpeed = BASE_SCROLL_SPEED * (player.isSpinning ? 0.2 : speedMultiplier);
    roadOffset += scrollSpeed;
    
    if (!player.isSpinning) {
        score += scrollSpeed * 0.1;
        fuel -= FUEL_DEPLETION_RATE * speedMultiplier;
    } else {
        fuel -= FUEL_DEPLETION_RATE; // still deplete while spinning
    }
    
    if (score >= WIN_SCORE) {
        gameOver(true);
        return;
    }
    
    if (fuel <= 0) {
        gameOver(false);
        return;
    }
    
    // Spawn enemies
    if (frames % 40 === 0 && Math.random() < 0.6 && score < WIN_SCORE - 80) {
        spawnEnemy();
    }
    
    for (let i = enemies.length - 1; i >= 0; i--) {
        let enemy = enemies[i];
        
        // Enemy moves relatively to the player's scroll speed
        enemy.y += (scrollSpeed - enemy.speed);
        
        // Remove enemies that fall off bottom
        if (enemy.y > canvas.height) {
            enemies.splice(i, 1);
        }
    }

    // Enemy traffic collision avoidance
    enemies.sort((a, b) => a.y - b.y);
    for (let i = 0; i < enemies.length; i++) {
        for (let j = i + 1; j < enemies.length; j++) {
            let eFront = enemies[i];
            let eBehind = enemies[j];
            if (Math.abs(eFront.x - eBehind.x) < CAR_WIDTH) {
                const minGap = CAR_HEIGHT + 15;
                if (eBehind.y - eFront.y < minGap) {
                    eBehind.y = eFront.y + minGap;
                    eBehind.speed = Math.min(eBehind.speed, eFront.speed);
                }
            }
        }
    }

    // Player collision check
    for (let i = enemies.length - 1; i >= 0; i--) {
        let enemy = enemies[i];
        if (!player.isSpinning && checkCollision(player, enemy)) {
            if (enemy.data.romaji === player.targetKana.romaji) {
                // Correct!
                fuel = Math.min(MAX_FUEL, fuel + FUEL_REWARD);
                player.targetKana = getRandomKana(); // Next challenge
                score += 50; // Bonus points
                
                // Visual feedback
                let originalColor = player.color;
                player.color = '#fff';
                setTimeout(() => player.color = originalColor, 100);
                
                enemies.splice(i, 1); // "Collect" the car
            } else {
                // Wrong!
                fuel -= FUEL_PENALTY;
                spinOut();
                enemies.splice(i, 1); // Crash and destroy
            }
        }
    }
    
    updateUI();
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawRoad();
    
    for (let enemy of enemies) {
        drawCar(enemy, false);
    }
    
    drawCar(player, true);

    // Left Margin: Course / Goal Progress Indicator
    const trackX = 25;
    const trackTopY = 65;
    const trackBottomY = 540;
    const trackLength = trackBottomY - trackTopY;
    const progress = Math.min(1.0, Math.max(0.0, score / WIN_SCORE));

    ctx.save();
    // G & S text
    ctx.font = 'bold 16px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ffeb3b';
    ctx.fillText('G', trackX, trackTopY - 14);
    ctx.fillStyle = '#ffffff';
    ctx.fillText('S', trackX, trackBottomY + 14);

    // Track line
    ctx.fillStyle = '#000000';
    ctx.fillRect(trackX - 3, trackTopY, 6, trackLength);
    ctx.fillStyle = '#dddddd';
    ctx.fillRect(trackX - 1, trackTopY, 2, trackLength);

    // Goal and Start bars
    ctx.fillStyle = '#ffeb3b';
    ctx.fillRect(trackX - 8, trackTopY - 1, 16, 3);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(trackX - 8, trackBottomY - 1, 16, 3);

    // Checkpoint ticks
    ctx.fillStyle = '#ffffff';
    for (let pct of [0.25, 0.5, 0.75]) {
        let ty = trackBottomY - pct * trackLength;
        ctx.fillRect(trackX - 5, ty - 1, 10, 2);
    }

    // Mini car marker
    const markerY = trackBottomY - progress * trackLength;
    ctx.fillStyle = '#000000';
    ctx.fillRect(trackX - 6, markerY - 8, 12, 16);
    ctx.fillStyle = '#ff3333';
    ctx.fillRect(trackX - 4, markerY - 6, 8, 12);
    ctx.fillStyle = '#ffff00';
    ctx.fillRect(trackX - 2, markerY - 3, 4, 6);
    ctx.restore();
}

function gameLoop() {
    update();
    draw();
    if (gameRunning) {
        requestAnimationFrame(gameLoop);
    }
}

window.addEventListener('keydown', (e) => {
    // Prevent default scrolling for game keys
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.code)) {
        e.preventDefault();
    }
    if (keys.hasOwnProperty(e.code)) {
        keys[e.code] = true;
    }
});

window.addEventListener('keyup', (e) => {
    if (keys.hasOwnProperty(e.code)) {
        keys[e.code] = false;
    }
});

restartBtn.addEventListener('click', init);

// Start game
init();
