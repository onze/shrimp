class Fetch {
//    async function post(url, data){
//        return fetch(url, {
//            method:'POST',
//            headers: {
//                'Content-Type': 'application/json;charset=utf-8',
//            },
//            body: JSON.stringify(data)
//        })
//    }
//
//    async function _delete(url, data){
//        return fetch(url, {
//            method:'DELETE',
//            headers: {
//                'Content-Type': 'application/json;charset=utf-8',
//            },
//            body: JSON.stringify(data)
//        })
//    }
//
//    async function put(url, data){
//        return fetch(url, {
//            method:'PUT',
//            headers: {
//                'Content-Type': 'application/json;charset=utf-8',
//            },
//            body: JSON.stringify(data)
//        })
//    }
//
//    async function get(url, rawParams){
//        let params = new URLSearchParams('')
//        if(rawParams) {
//            for(const [k,v] of Object.entries(rawParams)){
//                params.append(k,v)
//            }
//        }
//        let inlineParams = params.toString()
//        if(inlineParams.length > 0) {
//            url += '?' + inlineParams
//        }
//        return fetch(url, {
//            method:'GET',
//            headers: {
//                'Content-Type': 'application/json;charset=utf-8',
//            },
//        })
//    }
    static async get(url, rawParams){
        let params = new URLSearchParams('')
        if(rawParams) {
            for(const [k,v] of Object.entries(rawParams)){
                params.append(k,v)
            }
        }
        let inlineParams = params.toString()
        if(inlineParams.length > 0) {
            url += '?' + inlineParams
        }
        return fetch(url, {
            method:'GET',
            headers: {
                'Content-Type': 'application/json;charset=utf-8',
            },
        })
    }
}
