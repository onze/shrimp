class ControllerSocket {
    constructor() {
    }

    connect(){
        this.socketio = io("/ws/controller");
        this.socketio.on("connect", this.onConnect)
        this.socketio.on("error", this.onError)
        this.socketio.on("disconnect", this.onDisconnect)
        this.socketio.on("status", this.onStatus)
    }

    onConnect(event) {
        console.log(`Controller connected!`)
    }

    onError(event) {
        console.log(`Controller socket error:`, event)
    }

    onDisconnect(event) {
        console.log(`Controller socket disconnected:`, event)
    }

    onStatus(status) {
      console.log("onStatus", status);
    }

    sendCommands(rawCommands) {
        this.socketio.emit('commands', JSON.stringify(rawCommands))
    }
}

document.addEventListener('alpine:init', () => {
    console.log('alpine:init @Controller')
    Alpine.data('Controller', () => ({
        buffer: Alpine.reactive({}),
        socket: new ControllerSocket(),
        feedback: '<input feedback>',
        connectionStatus: Alpine.reactive({text:''}),
        init(){
            this.socket.onConnect = (event) => {this.connectionStatus.text = 'connected'}
            this.socket.onDisconnect = (event) => {this.connectionStatus.text = 'disconnected:' +event}
            this.socket.onError = (event) => {this.connectionStatus.text = 'error: '+event}
            this.socket.connect()
        },
        mouseDown: function(btn) {
            console.log(`mouseDown(${btn})`)
            this.socket.sendCommands([btn])
            this.buffer[btn] = true
            this.refreshOnScreenStatus()
        },
        mouseUp: function(btn) {
            console.log(`mouseUp(${btn})`)
            this.socket.sendCommands([btn+'-stop'])
            delete this.buffer[btn]
            this.refreshOnScreenStatus()
        },
        clearBuffer(){
            console.log(`clear buffer`)
            Object.keys(this.buffer).forEach(key => {
                this.socket.sendCommands([key+'-stop'])
                delete this.buffer[key]
            });
            this.refreshOnScreenStatus()
        },
        refreshOnScreenStatus: function() {
            let inputs = _.sortedUniq(Object.keys(this.buffer))
            if(inputs.length>0) {
                console.log('inputs', inputs)
                this.feedback = _.join(inputs, ',')
            } else {
                this.feedback = '-'
            }
        },
        swapElementLabels: function(e0, e1) {
            let save = e0.getAttribute('label');
            e0.setAttribute('label', e1.getAttribute('label'));
            e1.setAttribute('label', save);
        }
    }))
})
