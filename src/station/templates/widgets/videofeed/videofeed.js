document.addEventListener('alpine:init', () => {
    console.log('alpine:init @VideoFeed')
    Alpine.data('VideoFeed', () => ({
        jmuxer: new JMuxer({
            node: 'jmuxer_videofeed',
            mode: 'video',
            flushingTime: 0,
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
        videoSettings: Alpine.$persist('400x300@24').as('videofeed.videoSettings'),
        resetVideoFeed(){
            this.stopStream()
            this.startConnectionFlow()
        },
        stopStream(){
            console.log('Stopping video feed...')
            this.ws.close()
        },
        startConnectionFlow(){
            let this_ = this
            console.log('Requesting a video feed url...')

            let vs = this.videoSettings
            let feedUrl = 'http://{{SERVER_URL}}/videofeed/start'
            Fetch.get(feedUrl, {
                width: vs.slice(0, vs.indexOf('x')),
                height: vs.slice(vs.indexOf('x')+1, vs.indexOf('@')),
                fps: vs.slice(vs.indexOf('@')+1),
            })
            .then((r)=>r.json())
            .then(function(data){
                if(data.code!=0) {
                    throw new Error(`While requesting a videofeed on ${feedUrl}: ${data.code}/${data.error}`)
                }
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
