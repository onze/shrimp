document.addEventListener('alpine:init', () => {
    console.log('alpine:init @VideoFeed')
    Alpine.data('VideoFeed', () => ({
        jmuxer: new JMuxer({
            node: 'jmuxer_videofeed',
            mode: 'video',
            flushingTime: 100,
            clearBuffer: true,
            //fps:
            onReady(){
                console.log('jmuxer ready')
            },
            onError(){
                console.log('jmuxer error')
            },
            debug: false
        }),
        startConnectionFlow(){
            let this_ = this
            console.log('Requesting a video feed url...')
            Fetch.get('http://{{SERVER_URL}}/videofeed/start')
            .then((r)=>r.json())
            .then(function(data){
                console.log('Got a video feed in on', data.videofeed_url, this_)
                this_.connectToVideoFeed(data.videofeed_url)
            })
            .catch(function(error){
                console.error(error)
            })
        },
        connectToVideoFeed(videofeed_url){
            let ws = new WebSocket(videofeed_url);
            this.ws = ws
            ws.this_ = this
            ws.binaryType = 'arraybuffer';
            ws.addEventListener('open', function(e) {
                console.log(`Connected to videofeed @ ${e.target.url}`);
            });
            ws.addEventListener('message',function(event) {
                 this.this_.jmuxer.feed({
                     video: new Uint8Array(event.data)
                 });
            });
            ws.addEventListener('error', function(e) {
                console.log('Socket Error', e);
            });
        },
        init(){
        },
    }))
})
